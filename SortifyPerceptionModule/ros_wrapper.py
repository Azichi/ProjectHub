"""
ros_wrapper.py

Handles ROS 2 integration if available. If not, no ROS-related code is executed.
"""

import struct
from config import LOG

# Try to import ROS 2
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String

    USE_ROS = True # ROS 2 available
except ImportError:
    USE_ROS = False # ROS 2 not available

    class String:
        def __init__(self):
            self.data = ""

    class Node:
        def __init__(self, name: str):
            pass

        def create_publisher(self, *args, **kwargs):
            return None

        def destroy_node(self):
            pass

    class rclpy:
        @staticmethod
        def init():
            pass

        @staticmethod
        def shutdown():
            pass

# ROS 2 Interface class
SHAPE_IDX = {"circle": 0, "square": 1}
COLOR_IDX = {"red": 0, "blue": 1, "green": 2, "yellow": 3}


class ROSInterface:
    # Initialize ROS node and publisher
    def __init__(self, node_name="perception_controller"):
        self.enabled = USE_ROS
        self.node = Node(node_name) if USE_ROS else None
        self.publisher = (
            self.node.create_publisher(String, "object_data", 10) if self.node else None
        )

    def publish(self, shape: str, color: str, tid: int, x: int, y: int, z: int):
        # Publish data to ROS
        if not self.enabled or self.publisher is None:
            #LOG.info(f"[SEND] id={tid} shape={shape} color={color} xyz=({x},{y},{z})")
            return

        xyz_i16 = (int(round(x)), int(round(y)), int(round(z)))
        payload = struct.pack(
            "<H B B h h h B",
            tid,
            SHAPE_IDX.get(shape, 255),
            COLOR_IDX.get(color, 255),
            *xyz_i16,
        )
        msg = String()
        msg.data = payload.hex()
        self.publisher.publish(msg)

    def destroy(self):
        # Destroy ROS node
        if self.node and self.enabled:
            self.node.destroy_node()


# ROS 2 Initialization
def ros_init():
    if USE_ROS:
        rclpy.init()

# ROS 2 Shutdown
def ros_shutdown():
    if USE_ROS:
        rclpy.shutdown()
