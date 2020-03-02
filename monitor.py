#!/usr/bin/env python

import os
import subprocess

import rosnode
import rospy

import psutil
from system_monitor.msg import OS as OSMsg
from system_monitor.msg import Process as ProcessMsg
from system_monitor.msg import Storage as StorageMsg

try:
    from xmlrpc.client import ServerProxy
except ImportError:
    from xmlrpclib import ServerProxy


def ns_join(*names):
    return reduce(rospy.names.ns_join, names, "")


class Process:
    def __init__(self, name, pid, monitor_node_name):
        self.name = name
        self.proc = psutil.Process(pid)
        self.pub_process = rospy.Publisher(ns_join(monitor_node_name, "nodes",
                                           name[1:]), ProcessMsg,
                                           queue_size=20)

    def publish(self):
        msg_process = ProcessMsg()
        msg_process.cpu = self.proc.cpu_percent()
        msg_process.memory = self.proc.memory_info().rss
        msg_process.io_read = self.proc.io_counters().read_bytes
        msg_process.io_write = self.proc.io_counters().write_bytes
        self.pub_process.publish(msg_process)

    def alive(self):
        return self.proc.is_running()


if __name__ == "__main__":
    rospy.init_node("system_monitor")
    node_name = rospy.get_name()

    master = rospy.get_master()

    poll_period = rospy.get_param('~poll_period', 1.0)

    this_ip = os.environ.get("ROS_IP")

    node_map = {}
    ignored_nodes = set()

    pub_os = rospy.Publisher(node_name + "/os", OSMsg,
                             queue_size=20)

    while not rospy.is_shutdown():
        for node in rosnode.get_node_names():
            if node in node_map or node in ignored_nodes:
                continue

            node_api = rosnode.get_api_uri(master, node)[2]
            if not node_api:
                rospy.logerr("[system monitor] failed to get api of node %s"
                             "(%s)" % (node, node_api))
                continue

            local_node = "localhost" in node_api or \
                         "127.0.0.1" in node_api or \
                         (this_ip is not None and this_ip in node_api) or \
                         subprocess.check_output("hostname").strip() \
                         in node_api
            if not local_node:
                ignored_nodes.add(node)
                rospy.loginfo("[system monitor] ignoring node %s with URI %s" % (node, node_api))
                continue

            try:
                resp = ServerProxy(node_api).getPid('/NODEINFO')
            except:
                rospy.logerr("[system monitor] failed to get"
                             "pid of node %s (api is %s)" % (node, node_api))
            else:
                node_map[node] = Process(node, resp[2], node_name)
                rospy.loginfo("[system monitor] adding new node %s" % node)

        for node_name, node in list(node_map.items()):
            if node.alive():
                node.publish()
            else:
                rospy.logwarn("[system monitor] lost node %s" % node_name)
                del node_map[node_name]

        msg_os = OSMsg()
        msg_os.cpu = psutil.cpu_percent()
        vm = psutil.virtual_memory()
        msg_os.memory_available = vm.available
        msg_os.memory_used = vm.used
        msg_os.memory_free = vm.free
        msg_os.memory_active = vm.active
        msg_os.memory_inactive = vm.inactive
        msg_os.memory_buffers = vm.buffers
        msg_os.memory_cached = vm.cached
        pub_os.publish(msg_os)

        rospy.sleep(poll_period)
