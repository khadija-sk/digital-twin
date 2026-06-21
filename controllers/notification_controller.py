# controllers/notification_controller.py

import logging

class NotificationController:

    @staticmethod
    def notify(title, message, timeout=5):
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=timeout)
        except Exception as e:
            logging.getLogger(__name__).warning("Erreur lors de l'affichage de la notification")

    @staticmethod
    def checkin_reminder():
        NotificationController.notify("Check-in du jour", "Tu n'as pas encore fait ton check-in aujourd'hui !")

    @staticmethod
    def pomodoro_start():
        NotificationController.notify("Session started", "Focus 25 minutes - You can do it!")

    @staticmethod
    def pomodoro_done():
        NotificationController.notify("Pomodoro done!", "Great! Take a 5-minute break.")

    @staticmethod
    def break_done():
        NotificationController.notify("Break over", "Ready for a new session?")

    @staticmethod
    def badge_unlocked(badge_name, badge_icon="🏆"):
        NotificationController.notify(f"Badge unlocked: {badge_name}", f"You earned: {badge_name}!")