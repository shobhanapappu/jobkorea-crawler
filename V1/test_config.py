import configparser
config = configparser.ConfigParser()
config.read('config.ini')
print("Web URL:", config.get('web', 'url'))
print("Headless:", config.getboolean('crawling', 'headless'))
print("Output Folder:", config.get('export', 'output_folder'))