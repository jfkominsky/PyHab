import types
from pathlib import Path

from psychopy import monitors, visual
from psychopy_tobii_infant import (InfantStimuli, TobiiController,
                                   TobiiInfantController)
from tobii_research_addons import CalibrationValidationResult

cal_points = [(-0.4, 0.4), (-0.4, -0.4), (0.0, 0.0), (0.4, 0.4), (0.4, -0.4)]
infant_dir = Path(__file__).parents[2].joinpath("demo/infant")
cal_fname = ["cow.png", "elk.png", "hippo.png", "ladybug.png", "panda.png"]
cal_stims = [infant_dir.joinpath(x) for x in cal_fname]
val_fname = ["fan-yellow.png"]
val_stims = [infant_dir.joinpath(x) for x in val_fname]


class DummyCalibration:
    def __init__(self):
        pass

    def enter_calibration_mode(self):
        pass

    def leave_calibration_mode(self):
        pass

    def collect_data(self, *args):
        pass

    def discard_data(self):
        pass

    def compute_and_apply(self):
        # Returns A CalibrationResult object.
        return DummyCalibrationResult()


class DummyCalibrationResult:
    def __init__(self):
        self.status = "calibration_status_failure"
        self.calibration_points = []


class DummyValidation:
    is_collecting_data = False

    def __init__(self):
        pass

    def enter_validation_mode(self):
        pass

    def leave_validation_mode(self):
        pass

    def start_collecting_data(self, *args):
        pass

    def compute(self):
        return CalibrationValidationResult([], 0, 0, 0, 0, 0, 0)


class DummyController(TobiiController):
    def __init__(self, win):
        self.win = win
        self.numkey_dict = self._default_numkey_dict
        self.calibration_dot_size = self._default_calibration_dot_size[
            self.win.units]
        self.calibration_disc_size = self._default_calibration_disc_size[
            self.win.units]
        self.eyetracker = -1  # None will raise exceptions
        self.calibration = DummyCalibration()
        self.update_calibration = self._update_calibration_auto
        self.update_validation = self._update_validation_auto


class DummyInfantController(TobiiInfantController):
    def __init__(self, win):
        self.win = win
        self.numkey_dict = self._default_numkey_dict
        self.calibration_dot_size = self._default_calibration_dot_size[
            self.win.units]
        self.calibration_disc_size = self._default_calibration_disc_size[
            self.win.units]
        self.eyetracker = -1  # None will raise exceptions
        self.calibration = DummyCalibration()
        self.update_calibration = self._update_calibration_infant
        self.shrink_speed = 1
        self.update_validation = self._update_validation_infant


class TestCalib:
    """Test the presentation of stimuli."""
    def setup(self):
        self.mon = monitors.Monitor("dummy",
                                    width=12.8,
                                    distance=65,
                                    autoLog=False)
        self.win = visual.Window(size=[128, 128],
                                 units="norm",
                                 monitor=self.mon,
                                 fullscr=False,
                                 allowGUI=False,
                                 autoLog=False)

        self.controller = DummyController(self.win)

    def test_calibration_validation(self):
        self.controller.run_calibration(cal_points,
                                        focus_time=0.2,
                                        result_msg_color="black")

        def _test_run_validation(self,
                                 validation_points=None,
                                 focus_time=0.5,
                                 decision_key="space",
                                 show_results=False,
                                 save_to_file=True,
                                 result_msg_color="white"):

            # setup the procedure
            self.validation = DummyValidation()

            if validation_points is None:
                validation_points = self.original_calibration_points

            # clear the display
            self.win.flip()

            self.validation.enter_validation_mode()
            self.update_validation(validation_points=validation_points,
                                   _focus_time=focus_time)
            validation_result = self.validation.compute()
            self.validation.leave_validation_mode()
            self.win.flip()

            if not (save_to_file or show_results):
                return validation_result

            result_buffer = self._process_validation_result(validation_result)
            self._show_validation_result(result_buffer, show_results,
                                         save_to_file, decision_key,
                                         result_msg_color)
            return validation_result

        self.controller.run_validation = types.MethodType(
            _test_run_validation, self.controller)
        self.controller.run_validation(cal_points,
                                       show_results=True,
                                       save_to_file=False)


class TestCalibInfant:
    """Test the presentation of stimuli for infants."""
    def setup(self):
        self.mon = monitors.Monitor("dummy",
                                    width=12.8,
                                    distance=65,
                                    autoLog=False)
        self.win = visual.Window(size=[128, 128],
                                 units="norm",
                                 monitor=self.mon,
                                 fullscr=False,
                                 allowGUI=False,
                                 autoLog=False)

        self.controller = DummyInfantController(self.win)

    def test_calibration_validation(self):
        self.controller.run_calibration(cal_points,
                                        infant_stims=cal_stims,
                                        focus_time=0.2,
                                        result_msg_color="black")

        def _test_run_validation(self,
                                 validation_points=None,
                                 infant_stims=None,
                                 focus_time=0.5,
                                 decision_key="space",
                                 show_results=False,
                                 save_to_file=True,
                                 result_msg_color="white"):
            if self.update_validation is None:
                raise ModuleNotFoundError(
                    "tobii_research_addons is not found.")

            # setup the procedure
            self.validation = DummyValidation()

            if validation_points is None:
                validation_points = self.original_calibration_points

            if infant_stims is not None:
                self.targets = InfantStimuli(self.win, infant_stims)

            # clear the display
            self.win.flip()

            self.validation.enter_validation_mode()
            self.update_validation(validation_points=validation_points,
                                   _focus_time=focus_time)
            validation_result = self.validation.compute()
            self.validation.leave_validation_mode()
            self.win.flip()

            if not (save_to_file or show_results):
                return validation_result

            result_buffer = self._process_validation_result(validation_result)
            self._show_validation_result(result_buffer, show_results,
                                         save_to_file, decision_key,
                                         result_msg_color)

            return validation_result

        self.controller.run_validation = types.MethodType(
            _test_run_validation, self.controller)
        self.controller.run_validation(validation_points=cal_points,
                                       infant_stims=None,
                                       show_results=True,
                                       save_to_file=False)
        self.controller.run_validation(validation_points=cal_points,
                                       infant_stims=val_stims,
                                       show_results=True,
                                       save_to_file=False)
