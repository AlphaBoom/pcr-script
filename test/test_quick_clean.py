"""Quick clean's exit and Guild House stamina decisions, driven by synthetic screens."""
from unittest import TestCase
from unittest.mock import Mock, patch

from ui_fixtures import screen

from pcrscript.game_ui.screen import EventUIError
from pcrscript.tasks.task_adventure import QuickClean


class QuickCleanTests(TestCase):
    def run_task(self, *frames, collect=None):
        task = object.__new__(QuickClean)
        task.robot = Mock(_task_output='cache/agent/synthetic')
        task.action_squential = Mock()
        task.set_progress = Mock()
        ui = Mock()
        ui.capture.side_effect = list(frames)+[screen()]
        with patch('pcrscript.tasks.task_adventure.EventUI', return_value=ui), \
             patch('pcrscript.tasks.task_adventure.ToHomePage') as home, \
             patch('pcrscript.tasks.task_adventure.collect_produced_stamina', side_effect=collect) as house, \
             patch('pcrscript.tasks.task_adventure._enter_adventure_actions', return_value=[]):
            task.run(2)
        return task, home, house

    def test_always_verifies_it_left_the_catalogue(self):
        _, home, house = self.run_task(screen(('关卡一览', 480, 42)))
        house.assert_not_called()
        home.return_value.run.assert_called_once_with(timeout=60)

    def test_stamina_warning_collects_the_house_once_then_reopens(self):
        warning = screen(('由于体力不足，因此有不能进行的关卡。', 250, 470))
        task, home, house = self.run_task(warning, collect=[dict(before=0, after=100)])
        house.assert_called_once()
        self.assertEqual(home.return_value.run.call_count, 3)

    def test_failed_collection_still_sweeps_with_existing_stamina(self):
        warning = screen(('由于体力不足，因此有不能进行的关卡。', 250, 470))
        task, _, house = self.run_task(warning, collect=EventUIError('公会之家领取回执超时'))
        house.assert_called_once()
        self.assertGreaterEqual(task.action_squential.call_count, 4)
