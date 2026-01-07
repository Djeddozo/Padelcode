import time

from booking_scheduler import BookingScheduler


if __name__ == "__main__":
    scheduler = BookingScheduler()
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
