import os
import sqlite3
import logging
import threading
import time
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class AutoBackup:
    def __init__(self):
        self.db_file = 'bot_data.db'
        self.backup_dir = '/tmp/db_backups'
        self._ensure_backup_dir()
        
    def _ensure_backup_dir(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def check_and_restore(self):
        """بررسی و بازیابی خودکار دیتابیس"""
        try:
            # اگر دیتابیس وجود ندارد یا خراب است
            if not os.path.exists(self.db_file) or not self.is_db_healthy():
                logger.warning("⚠️ دیتابیس مشکل دارد، در حال بازیابی...")
                self.restore_backup()
                return True
            return True
        except Exception as e:
            logger.error(f"❌ خطا در بررسی دیتابیس: {e}")
            return False
    
    def is_db_healthy(self):
        """بررسی سلامت دیتابیس"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except:
            return False
    
    def create_backup(self):
        """ایجاد پشتیبان"""
        try:
            if os.path.exists(self.db_file) and self.is_db_healthy():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_dir, f'backup_{timestamp}.db')
                shutil.copy2(self.db_file, backup_file)
                
                # حذف پشتیبان‌های قدیمی
                self._clean_old_backups()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطا در پشتیبان‌گیری: {e}")
            return False
    
    def restore_backup(self):
        """بازیابی از آخرین پشتیبان"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('backup_') and file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backups.append((file_path, os.path.getctime(file_path)))
            
            if backups:
                backups.sort(key=lambda x: x[1], reverse=True)
                latest_backup = backups[0][0]
                shutil.copy2(latest_backup, self.db_file)
                logger.info(f"✅ دیتابیس از پشتیبان بازیابی شد: {latest_backup}")
                return True
            else:
                logger.warning("⚠️ هیچ پشتیبانی برای بازیابی وجود ندارد")
                return False
        except Exception as e:
            logger.error(f"❌ خطا در بازیابی: {e}")
            return False
    
    def _clean_old_backups(self):
        """حذف پشتیبان‌های قدیمی"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('backup_') and file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backups.append((file_path, os.path.getctime(file_path)))
            
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # فقط ۲ پشتیبان آخر نگه دار
            for backup_file, _ in backups[2:]:
                os.remove(backup_file)
        except Exception as e:
            logger.error(f"❌ خطا در پاک‌سازی پشتیبان‌ها: {e}")
    
    def start_auto_backup(self):
        """شروع پشتیبان‌گیری خودکار"""
        def backup_loop():
            while True:
                try:
                    # اول بررسی کن دیتابیس سالم باشه
                    self.check_and_restore()
                    
                    # سپس پشتیبان بگیر
                    self.create_backup()
                    
                    # ۱۰ دقیقه صبر کن
                    time.sleep(600)
                    
                except Exception as e:
                    logger.error(f"❌ خطا در حلقه پشتیبان‌گیری: {e}")
                    time.sleep(60)
        
        # شروع در ترد جداگانه
        backup_thread = threading.Thread(target=backup_loop, daemon=True)
        backup_thread.start()
        logger.info("🚀 پشتیبان‌گیری خودکار شروع شد (هر ۱۰ دقیقه)")

# نمونه جهانی
auto_backup = AutoBackup()
