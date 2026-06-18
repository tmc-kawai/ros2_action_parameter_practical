"""AutoCharge action client.

Sends a goal whose target comes from the `target_percent` parameter, e.g.:
    ros2 run action_param_demo auto_charge_client --ros-args -p target_percent:=90
Prints streamed feedback and the final result, then exits.
"""

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_param_interfaces.action import AutoCharge


class AutoChargeClient(Node):

    def __init__(self):
        super().__init__('auto_charge_client')
        self.declare_parameter('target_percent', 80)
        self._client = ActionClient(self, AutoCharge, 'auto_charge')

    def _feedback_cb(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'Feedback: {fb.current_percent}% ({fb.status})')


def main(args=None):
    rclpy.init(args=args)
    node = AutoChargeClient()

    target = node.get_parameter('target_percent').value
    node.get_logger().info('Waiting for action server /auto_charge ...')
    node._client.wait_for_server()

    goal = AutoCharge.Goal()
    goal.target_percent = int(target)
    node.get_logger().info(f'Sending goal: target_percent={target}')

    send_future = node._client.send_goal_async(
        goal, feedback_callback=node._feedback_cb)
    rclpy.spin_until_future_complete(node, send_future)
    goal_handle = send_future.result()

    if not goal_handle.accepted:
        node.get_logger().warn('Goal was rejected by the server')
        node.destroy_node()
        rclpy.shutdown()
        return

    node.get_logger().info('Goal accepted, waiting for result ...')
    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future)
    result = result_future.result().result

    node.get_logger().info(
        f'Result: success={result.success}, '
        f'message="{result.message}", final_percent={result.final_percent}')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
