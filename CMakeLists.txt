cmake_minimum_required(VERSION 2.8.3)
project(system_monitor)

find_package(catkin REQUIRED COMPONENTS
  rospy
  message_generation
  genmsg
)

add_message_files(
  FILES
    OS.msg
    Process.msg
    Storage.msg
)

generate_messages(
  DEPENDENCIES
)

catkin_package(
  CATKIN_DEPENDS
    message_runtime
)

install(PROGRAMS
   monitor.py
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  PATTERN *~ EXCLUDE
)
