from pathlib import Path
import time
import threading
import configparser
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class SiteCrawler(threading.Thread):
    """백그라운드에서 사이트를 주기적으로 확인하여 신규 상담을 감지합니다.

    프로그램 시작 시 첫 번째 행을 기준점으로 설정하고,
    그 이후 새롭게 추가되는 행들만 문자 발송 대상으로 처리합니다.
    """

    def __init__(self, cfg: configparser.ConfigParser, on_new_callback=None, on_status_callback=None):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.on_new_callback = on_new_callback
        self.on_status_callback = on_status_callback  # 상태 업데이트 콜백
        self._stop = threading.Event()
        self.baseline_consultation_no = None  # 기준점이 되는 첫 번째 상담 번호
        self.known_consultation_nos = set()  # 이미 확인한 상담 No들
        self.start()

    def _init_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        return driver

    def _get_first_consultation_no(self, driver):
        """현재 테이블의 첫 번째 상담 번호를 가져옵니다"""
        try:
            xpath_no = '/html/body/section/div/div[2]/table/tbody/tr[1]/td[1]'
            no_element = driver.find_elements(By.XPATH, xpath_no)
            if no_element:
                consultation_no = no_element[0].text.strip()
                if consultation_no:
                    return consultation_no
        except Exception as e:
            logging.error(f"첫 번째 상담 번호 확인 중 오류: {e}")
        return None

    def _scan_all_consultations(self, driver):
        """테이블 전체를 스캔하여 모든 상담 정보를 수집"""
        consultations = []
        try:
            # 테이블의 모든 행을 확인 (최대 50행까지)
            for row_idx in range(1, 51):  # tr[1]부터 tr[50]까지
                try:
                    xpath_no = f'/html/body/section/div/div[2]/table/tbody/tr[{row_idx}]/td[1]'
                    xpath_phone = f'/html/body/section/div/div[2]/table/tbody/tr[{row_idx}]/td[16]'
                    
                    # 해당 행이 존재하는지 확인
                    no_element = driver.find_elements(By.XPATH, xpath_no)
                    if not no_element:
                        break  # 더 이상 행이 없으면 종료
                    
                    consultation_no = no_element[0].text.strip()
                    if not consultation_no or consultation_no == "":
                        break  # 빈 행이면 종료
                    
                    phone_element = driver.find_elements(By.XPATH, xpath_phone)
                    phone = phone_element[0].text.strip() if phone_element else ""
                    
                    if consultation_no and phone:
                        consultations.append({
                            "no": consultation_no,
                            "phone": phone,
                            "row": row_idx
                        })
                    
                except Exception as e:
                    # 개별 행 처리 중 오류가 발생해도 계속 진행
                    logging.debug(f"행 {row_idx} 처리 중 오류: {e}")
                    break
            
            logging.info(f"테이블 스캔 완료: 총 {len(consultations)}건 확인")
            return consultations
            
        except Exception as e:
            logging.error(f"테이블 스캔 중 오류: {e}")
            return []

    def _filter_new_consultations(self, consultations):
        """기준점보다 새로운 상담들만 필터링"""
        if not self.baseline_consultation_no:
            return []
        
        new_consultations = []
        try:
            baseline_no = int(self.baseline_consultation_no) if self.baseline_consultation_no.isdigit() else 0
            
            for consultation in consultations:
                consultation_no = consultation["no"]
                if consultation_no.isdigit():
                    current_no = int(consultation_no)
                    # 기준점보다 큰 번호이고, 아직 처리하지 않은 상담만 선택
                    if current_no > baseline_no and consultation_no not in self.known_consultation_nos:
                        new_consultations.append(consultation)
                        self.known_consultation_nos.add(consultation_no)
            
        except Exception as e:
            logging.error(f"신규 상담 필터링 중 오류: {e}")
        
        return new_consultations

    def run(self):
        url = self.cfg.get("web", "url")
        username = self.cfg.get("web", "username")
        password = self.cfg.get("web", "password")
        interval = self.cfg.getint("web", "refresh_interval", fallback=60)

        logging.info("크롤러 시작 (첫 번째 행 기준 모드)")
        logging.info(f"URL: {url}")
        logging.info(f"새로고침 간격: {interval}초")

        driver = self._init_driver()
        
        try:
            logging.info("웹사이트 접속 중...")
            driver.get(url)
            
            # 로그인 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="id"]'))
            )
            
            logging.info("로그인 시도 중...")
            driver.find_element(By.XPATH, '//*[@id="id"]').send_keys(username)
            driver.find_element(By.XPATH, '//*[@id="pwd"]').send_keys(password)
            driver.find_element(By.XPATH, '//*[@id="pwd"]').submit()
            
            # 로그인 후 페이지 로드 대기
            time.sleep(3)
            
            # 테이블이 로드될 때까지 대기
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/section/div/div[2]/table/tbody/tr[1]/td[1]'))
                )
                logging.info("로그인 성공, 테이블 감지됨")
            except:
                logging.error("테이블을 찾을 수 없습니다. 로그인이 실패했거나 페이지 구조가 변경되었습니다.")
                return

            # 🔥 핵심: 프로그램 시작 시 첫 번째 행을 기준점으로 설정
            self.baseline_consultation_no = self._get_first_consultation_no(driver)
            if self.baseline_consultation_no:
                logging.info(f"📍 기준점 설정: 첫 번째 상담 No.{self.baseline_consultation_no}")
                logging.info(f"🚀 이제부터 No.{self.baseline_consultation_no}보다 큰 번호의 신규 상담에 대해 문자 발송됩니다")
                
                # 메인 윈도우에 기준점 설정 완료 알림
                if self.on_status_callback:
                    self.on_status_callback(f"✅ 기준점 설정 완료: 첫 번째 상담 No.{self.baseline_consultation_no}")
                    self.on_status_callback(f"🎯 이제부터 No.{self.baseline_consultation_no}보다 큰 번호에 대해 자동 문자 발송됩니다")
            else:
                logging.warning("⚠️ 기준점을 설정할 수 없습니다. 첫 번째 행이 비어있거나 오류가 발생했습니다.")
                if self.on_status_callback:
                    self.on_status_callback("❌ 기준점 설정 실패: 첫 번째 행이 비어있거나 오류가 발생했습니다")
                return

            check_count = 0
            
            while not self._stop.is_set():
                try:
                    check_count += 1
                    
                    # 페이지 새로고침
                    driver.refresh()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/section/div/div[2]/table/tbody/tr[1]/td[1]'))
                    )
                    
                    # 전체 테이블 스캔
                    current_consultations = self._scan_all_consultations(driver)
                    
                    # 기준점보다 새로운 상담들만 필터링
                    new_consultations = self._filter_new_consultations(current_consultations)
                    
                    # 현재 첫 번째 행 확인 (기준점 업데이트용)
                    current_first_no = self._get_first_consultation_no(driver)
                    
                    logging.info(f"체크 #{check_count} - 총 {len(current_consultations)}건, 신규 {len(new_consultations)}건 (기준: No.{self.baseline_consultation_no}, 현재 첫째: No.{current_first_no})")
                    
                    if new_consultations:
                        # 신규 상담들을 번호 순으로 정렬 (오래된 것부터 처리)
                        new_consultations.sort(key=lambda x: int(x["no"]) if x["no"].isdigit() else 0)
                        
                        for consultation in new_consultations:
                            logging.info(f"🚨 신규 상담 감지! No.{consultation['no']}, 전화번호: {consultation['phone']}")
                        
                        if self.on_new_callback:
                            self.on_new_callback(new_consultations)
                            logging.info(f"📱 문자발송 콜백 함수 호출 완료 ({len(new_consultations)}건)")
                    else:
                        logging.info("신규 상담 없음")
                        
                except Exception as e:
                    logging.error(f"크롤러 에러: {e}")
                    # 에러가 발생해도 계속 시도
                    
                logging.info(f"{interval}초 대기 중...")
                time.sleep(interval)

        except Exception as e:
            logging.error(f"크롤러 초기화 실패: {e}")
        finally:
            driver.quit()
            logging.info("크롤러 종료")

    def stop(self):
        self._stop.set()
