"""
Account Deletion Scheduled Job

Processes pending account deletions that have passed their grace period.
This job should be run daily to ensure compliance with DPDP Act requirements.

Requirements: 15.4 - Account deletion with data removal within 30 days
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

from app.core.database import SessionLocal
from app.services.privacy.account_deletion_service import AccountDeletionService


logger = logging.getLogger(__name__)


class AccountDeletionJob:
    """
    Scheduled job for processing account deletions.
    
    This job:
    1. Finds accounts with deletion requests past their grace period
    2. Executes the deletion for each account
    3. Logs the results for audit purposes
    
    Requirements: 15.4
    """
    
    def __init__(self):
        """Initialize the account deletion job."""
        self.deletion_service = AccountDeletionService()
        logger.info("Initialized AccountDeletionJob")
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the account deletion job.
        
        Returns:
            Dictionary with job execution summary
        """
        logger.info("Starting account deletion job")
        start_time = datetime.utcnow()
        
        db = SessionLocal()
        try:
            # Get pending deletions
            pending_deletions = self.deletion_service.get_pending_deletions(
                db=db,
                due_before=datetime.utcnow()
            )
            
            if not pending_deletions:
                logger.info("No pending deletions found")
                return {
                    "status": "completed",
                    "started_at": start_time.isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "pending_count": 0,
                    "processed_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "errors": []
                }
            
            logger.info(f"Found {len(pending_deletions)} account(s) pending deletion")
            
            # Process each deletion
            results = {
                "status": "completed",
                "started_at": start_time.isoformat(),
                "pending_count": len(pending_deletions),
                "processed_count": 0,
                "success_count": 0,
                "error_count": 0,
                "errors": [],
                "deleted_accounts": []
            }
            
            for deletion in pending_deletions:
                user_id = deletion["user_id"]
                try:
                    logger.info(f"Processing deletion for user {user_id}")
                    
                    deletion_result = self.deletion_service.execute_account_deletion(
                        db=db,
                        user_id=user_id,
                        force=False  # Respect grace period
                    )
                    
                    results["success_count"] += 1
                    results["deleted_accounts"].append({
                        "user_id": user_id,
                        "name": deletion["name"],
                        "deleted_at": deletion_result["deleted_at"],
                        "data_removed": deletion_result["data_removed"]
                    })
                    
                    logger.info(
                        f"Successfully deleted account for user {user_id}. "
                        f"Data removed: {deletion_result['data_removed']}"
                    )
                
                except Exception as e:
                    results["error_count"] += 1
                    error_msg = f"Failed to delete account for user {user_id}: {str(e)}"
                    results["errors"].append({
                        "user_id": user_id,
                        "error": str(e)
                    })
                    logger.error(error_msg, exc_info=True)
                
                finally:
                    results["processed_count"] += 1
            
            results["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"Account deletion job completed. "
                f"Processed: {results['processed_count']}, "
                f"Success: {results['success_count']}, "
                f"Errors: {results['error_count']}"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Account deletion job failed: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "started_at": start_time.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        
        finally:
            db.close()


def run_account_deletion_job() -> Dict[str, Any]:
    """
    Convenience function to run the account deletion job.
    
    Returns:
        Job execution summary
    """
    job = AccountDeletionJob()
    return job.run()


if __name__ == "__main__":
    # Allow running the job directly for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_account_deletion_job()
    print(f"\nJob Result:\n{result}")
