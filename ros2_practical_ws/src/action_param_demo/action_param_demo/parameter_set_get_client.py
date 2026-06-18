"""Programmatically set & get parameters of another node.

Targets the running `auto_charge_server` and uses the async parameter client
to set a couple of parameters and read several back. Start the server first:
    ros2 run action_param_demo auto_charge_server
"""

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.parameter_client import AsyncParameterClient


def main(args=None):
    rclpy.init(args=args)
    node = Node('parameter_set_get_client')
    target = 'auto_charge_server'
    client = AsyncParameterClient(node, target)

    node.get_logger().info(f'Waiting for parameter services of /{target} ...')
    if not client.wait_for_services(timeout_sec=5.0):
        node.get_logger().error(
            f'/{target} is not available. Start it first with: '
            'ros2 run action_param_demo auto_charge_server')
        node.destroy_node()
        rclpy.shutdown()
        return

    # --- set parameters ---
    set_future = client.set_parameters([
        Parameter('charge_step', Parameter.Type.INTEGER, 7),
        Parameter('station_name', Parameter.Type.STRING, 'client_station'),
    ])
    rclpy.spin_until_future_complete(node, set_future)
    for name, res in zip(['charge_step', 'station_name'],
                         set_future.result().results):
        node.get_logger().info(
            f'set {name}: successful={res.successful} {res.reason}'.rstrip())

    # --- get parameters ---
    get_future = client.get_parameters(
        ['charge_step', 'feedback_period_sec', 'station_name'])
    rclpy.spin_until_future_complete(node, get_future)
    values = get_future.result().values
    node.get_logger().info(
        f'get -> charge_step={values[0].integer_value}, '
        f'feedback_period_sec={values[1].double_value}, '
        f'station_name="{values[2].string_value}"')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
