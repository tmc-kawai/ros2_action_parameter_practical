"""AutoCharge action server with runtime-configurable parameters.

Demonstrates:
  * an action server (`/auto_charge`) that streams feedback while "charging",
  * declared parameters (charge_step / feedback_period_sec / station_name),
  * a parameter validation callback that rejects invalid values.
"""

import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from rcl_interfaces.msg import SetParametersResult

from action_param_interfaces.action import AutoCharge


class AutoChargeServer(Node):

    def __init__(self):
        super().__init__('auto_charge_server')

        # --- parameters (changeable at runtime via `ros2 param set`) ---
        self.declare_parameter('charge_step', 10)            # % per step
        self.declare_parameter('feedback_period_sec', 1.0)   # seconds between feedback
        self.declare_parameter('station_name', 'default_station')

        # validate every parameter change
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self._action_server = ActionServer(
            self,
            AutoCharge,
            'auto_charge',
            execute_callback=self._execute,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )

        station = self.get_parameter('station_name').value
        self.get_logger().info(f"AutoCharge server ready at station '{station}'.")

    # ------------------------------------------------------------------ #
    # parameter validation
    # ------------------------------------------------------------------ #
    def _on_set_parameters(self, params):
        for p in params:
            if p.name == 'charge_step':
                if int(p.value) <= 0:
                    return SetParametersResult(
                        successful=False,
                        reason='charge_step must be a positive integer')
            elif p.name == 'feedback_period_sec':
                if float(p.value) <= 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason='feedback_period_sec must be > 0')
            elif p.name == 'station_name':
                if not isinstance(p.value, str) or p.value == '':
                    return SetParametersResult(
                        successful=False,
                        reason='station_name must be a non-empty string')
        return SetParametersResult(successful=True)

    # ------------------------------------------------------------------ #
    # action callbacks
    # ------------------------------------------------------------------ #
    def _goal_callback(self, goal_request):
        target = goal_request.target_percent
        if target < 0 or target > 100:
            self.get_logger().warn(
                f'Reject goal: target_percent={target} is out of [0, 100]')
            return GoalResponse.REJECT
        self.get_logger().info(f'Accept goal: charge up to {target}%')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def _execute(self, goal_handle):
        target = goal_handle.request.target_percent
        current = 0
        result = AutoCharge.Result()

        while current < target:
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.message = 'Charging canceled'
                result.final_percent = current
                self.get_logger().info('Goal canceled')
                return result

            # read parameters fresh each step so live changes take effect
            step = self.get_parameter('charge_step').value
            period = self.get_parameter('feedback_period_sec').value
            station = self.get_parameter('station_name').value

            current = min(current + step, target)

            feedback = AutoCharge.Feedback()
            feedback.current_percent = current
            feedback.status = f'[{station}] charging... {current}%'
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(feedback.status)

            if current < target:
                time.sleep(float(period))

        goal_handle.succeed()
        result.success = True
        result.message = (
            f'Charged to {target}% at '
            f'{self.get_parameter("station_name").value}')
        result.final_percent = current
        self.get_logger().info(result.message)
        return result


def main(args=None):
    rclpy.init(args=args)
    node = AutoChargeServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
