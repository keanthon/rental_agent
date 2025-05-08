import schedule
import time
import logging
import threading
from datetime import datetime
from app.services.matching_service import MatchingService

class SchedulerService:
    """Service for scheduling and running background tasks"""
    
    def __init__(self, api_key=None):
        self.matching_service = MatchingService(api_key)
        self.is_running = False
        self.scheduler_thread = None
    
    def setup_scheduled_jobs(self):
        """Setup scheduled jobs to run twice daily"""
        # Schedule first run at 9:00 AM
        schedule.every().day.at("09:00").do(self._run_matching_job)
        
        # Schedule second run at 4:00 PM
        schedule.every().day.at("16:00").do(self._run_matching_job)
        
        logging.info("Scheduled matching jobs set for 9:00 AM and 4:00 PM daily")
    
    def _run_matching_job(self):
        """Run the matching job and log results"""
        logging.info(f"Running scheduled matching job at {datetime.now()}")
        
        try:
            result = self.matching_service.find_matches_for_all_users()
            
            logging.info(f"Matching job completed: Found {result['total_new_matches']} new matches for {result['total_users']} users")
            
            # Log any errors
            for user_result in result.get('user_results', []):
                if user_result.get('errors'):
                    logging.warning(f"Errors for user {user_result.get('user_id')}: {user_result.get('errors')}")
            
            return result
        except Exception as e:
            logging.error(f"Error running matching job: {str(e)}")
            return None
    
    def run_now(self):
        """Run the matching job immediately (for testing or manual trigger)"""
        return self._run_matching_job()
    
    def start(self):
        """Start the scheduler in a separate thread"""
        if self.is_running:
            logging.warning("Scheduler is already running")
            return False
        
        self.setup_scheduled_jobs()
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logging.info("Scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logging.warning("Scheduler is not running")
            return False
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1.0)
        
        logging.info("Scheduler stopped")
        return True
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute