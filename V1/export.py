import pandas as pd
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %= (levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DataExporter:
    """Handles exporting crawled data to Excel."""

    def __init__(self, output_folder='output'):
        self.output_folder = Path(output_folder)
        self.logger = logging.getLogger(__name__)

    def export_to_excel(self, posts, filename='jobkorea_data.xlsx'):
        """Export posts to an Excel file."""
        try:
            # Ensure output folder exists
            self.output_folder.mkdir(parents=True, exist_ok=True)

            # Prepare data for Excel
            data = []
            for post in posts:
                job_details = post.get('recruitment_details', {})
                data.append({
                    'ID': post.get('id', ''),
                    'Title': post.get('title', ''),
                    'Company': post.get('company', ''),
                    'Details': '; '.join(post.get('details', [])),  # Join list of details
                    'Details URL': post.get('details_url', ''),
                    'Manager Info': post.get('manager_info', ''),
                    'Experience': job_details.get('experience', 'Not found'),
                    'Education': job_details.get('education', 'Not found'),
                    'Employment Type': job_details.get('employment_type', 'Not found'),
                    'Employment Info': job_details.get('employment_info', 'Not found'),
                    'Salary': job_details.get('salary', 'Not found'),
                    'Region': job_details.get('region', 'Not found'),
                    'Working Hours': job_details.get('working_hours', 'Not found'),
                    'Industry': job_details.get('industry', 'Not found'),
                    'Year Established': job_details.get('year_established', 'Not found'),
                    'Corporate Form': job_details.get('corporate_form', 'Not found')
                })

            # Create DataFrame and save to Excel
            df = pd.DataFrame(data)
            output_path = self.output_folder / filename
            df.to_excel(output_path, index=False, engine='openpyxl')
            self.logger.info(f"Exported {len(posts)} posts to {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Failed to export to Excel: {e}")
            raise