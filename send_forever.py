from helpers import send_all_due_reminders

if __name__ == '__main__':
  import time
  while True:
    print('.', end='')
    send_all_due_reminders()
    time.sleep(10)
