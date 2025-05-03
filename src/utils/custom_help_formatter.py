import argparse

class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)

        # Join the option strings with commas (with space around the commas)
        parts = [opt for opt in action.option_strings]
        return ' , '.join(parts)
