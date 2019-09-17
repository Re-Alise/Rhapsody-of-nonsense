from controller import Controller

if __name__ == "__main__":
    controller = Controller(debug=True, replay_path='/Users/kanzakihideyoshi/Desktop/tdk23/records/1568642905/original.avi')
    controller.record.start()
    controller.mission_start()
    input('')