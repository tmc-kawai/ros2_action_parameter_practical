"""Parameter-callback demo node.

Publishes a decorated greeting on `chatter` every second. The decoration string
is a parameter that can be changed live, e.g.:
    ros2 param set /param_talker decoration "***"
The on-set-parameters callback applies the new value immediately.
"""

import rclpy
from rclpy.node import Node

from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import String


class ParamTalker(Node):

    def __init__(self):
        super().__init__('param_talker')
        self.declare_parameter('decoration', '---')
        self._decoration = self.get_parameter('decoration').value
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self._pub = self.create_publisher(String, 'chatter', 10)
        self._count = 0
        self.create_timer(1.0, self._on_timer)
        self.get_logger().info('param_talker started.')

    def _on_set_parameters(self, params):
        for p in params:
            if p.name == 'decoration':
                if not isinstance(p.value, str):
                    return SetParametersResult(
                        successful=False, reason='decoration must be a string')
                self._decoration = p.value
                self.get_logger().info(f'decoration updated to "{p.value}"')
        return SetParametersResult(successful=True)

    def _on_timer(self):
        msg = String()
        msg.data = f'{self._decoration} Hello {self._count} {self._decoration}'
        self._pub.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self._count += 1


def main(args=None):
    rclpy.init(args=args)
    node = ParamTalker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
