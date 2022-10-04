import atexit
import os
from datetime import datetime

import numpy as np
import tobii_research as tr
from PIL import Image, ImageDraw
from psychopy import core, event, visual
from psychopy.tools.monitorunittools import cm2pix, deg2pix, pix2cm, pix2deg

_has_addons = True
# yapf: disable
try:
    from tobii_research_addons import (
        ScreenBasedCalibrationValidation, Point2)
    from math import ceil
except ModuleNotFoundError:
    try:
        from .tobii_research_addons import (
            ScreenBasedCalibrationValidation, Point2)
        from math import ceil
    except ModuleNotFoundError:
        _has_addons = False
# yapf: enable
__version__ = "0.8.0"


class InfantStimuli:
    """Stimuli for infant-friendly calibration and validation.

    Args:
        win: psychopy.visual.Window object.
        infant_stims: list of image files.
        shuffle: whether to shuffle the presentation order of the stimuli.
            Default is True.
        *kwargs: other arguments to pass into psychopy.visual.ImageStim.

    Attributes:
        present_order: the presentation order of the stimuli.
    """
    def __init__(self, win, infant_stims, shuffle=True, *kwargs):
        self.win = win
        self.stims = dict((i, visual.ImageStim(self.win, image=stim, *kwargs))
                          for i, stim in enumerate(infant_stims))
        self.stim_size = dict(
            (i, image_stim.size) for i, image_stim in self.stims.items())
        self.present_order = [*self.stims]
        if shuffle:
            np.random.shuffle(self.present_order)

    def get_stim(self, idx):
        """Get the stimulus by presentation order.

        Args:
        idx: index of the presentation order. If it is larger than the number
            of provided image files, it will re-iterate.

        Returns:
            psychopy.visual.ImageStim
        """
        return self.stims[self.present_order[idx % len(self.present_order)]]

    def get_stim_original_size(self, idx):
        """Get the original size of the stimulus by presentation order.

        Args:
        idx: index of the presentation order. If it is larger than the number
            of provided image files, it will re-iterate.

        Returns:
            The size (width, height) of the stimulus in the stimulus units.
        """
        return self.stim_size[self.present_order[idx %
                                                 len(self.present_order)]]


class TobiiController:
    """Tobii controller for PsychoPy.

        tobii_research are required for this module.

    Args:
        win: psychopy.visual.Window object.
        id: the id of eyetracker. Default is 0 (use the first found eye
            tracker).
        filename: the name of the data file.

    Attributes:
        shrink_speed: the shrinking speed of target in calibration.
            Default is 1.5.
        calibration_dot_size: the size of the central dot in the
            calibration target. Default is _default_calibration_dot_size
            according to the units of self.win.
        calibration_dot_color: the color of the central dot in the
            calibration target. Default is grey.
        calibration_disc_size: the size of the disc in the
            calibration target. Default is _default_calibration_disc_size
            according to the units of self.win.
        calibration_disc_color: the color of the disc in the
            calibration target. Default is deep blue.
        calibration_target_min: the minimum size of the calibration target.
            Default is 0.2.
        numkey_dict: keys used for calibration. Default is the number pad.
            If it is changed, the keys in calibration result will not
            update accordingly (my bad), be cautious!
        update_calibration: the presentation of calibration target.
            Default is auto calibration.
    """
    _default_numkey_dict = {
        "0": -1,
        "num_0": -1,
        "1": 0,
        "num_1": 0,
        "2": 1,
        "num_2": 1,
        "3": 2,
        "num_3": 2,
        "4": 3,
        "num_4": 3,
        "5": 4,
        "num_5": 4,
        "6": 5,
        "num_6": 5,
        "7": 6,
        "num_7": 6,
        "8": 7,
        "num_8": 7,
        "9": 8,
        "num_9": 8,
    }
    _default_calibration_dot_size = {
        "norm": 0.02,
        "height": 0.01,
        "pix": 10.0,
        "degFlatPos": 0.25,
        "deg": 0.25,
        "degFlat": 0.25,
        "cm": 0.25,
    }
    _default_calibration_disc_size = {
        "norm": 0.08,
        "height": 0.04,
        "pix": 40.0,
        "degFlatPos": 1.0,
        "deg": 1.0,
        "degFlat": 1.0,
        "cm": 1.0,
    }
    _shrink_speed = 1.5
    _shrink_sec = 3 / _shrink_speed
    calibration_dot_color = (0, 0, 0)
    calibration_disc_color = (-1, -1, 0)
    calibration_target_min = 0.2
    update_calibration = None
    update_validation = None
    recording = False
    datafile = None
    validation_result_buffers = None

    def __init__(self, win, id=0, filename="gaze_TOBII_output.tsv"):
        self.eyetracker_id = id
        self.win = win
        self.filename = filename
        # FIXME: self.numkey_dict is not updated accordingly
        self.numkey_dict = self._default_numkey_dict
        self.calibration_dot_size = self._default_calibration_dot_size[
            self.win.units]
        self.calibration_disc_size = self._default_calibration_disc_size[
            self.win.units]

        eyetrackers = tr.find_all_eyetrackers()

        if len(eyetrackers) == 0:
            raise RuntimeError("No Tobii eyetrackers detected.")

        try:
            self.eyetracker = eyetrackers[self.eyetracker_id]
        except IndexError:
            raise ValueError(
                "Invalid eyetracker ID {}\n({} eyetrackers found)".format(
                    self.eyetracker_id, len(eyetrackers)))

        self.calibration = tr.ScreenBasedCalibration(self.eyetracker)
        self.update_calibration = self._update_calibration_auto
        if _has_addons:
            self.update_validation = self._update_validation_auto
        self.gaze_data = []
        atexit.register(self.close)

    def _on_gaze_data(self, gaze_data):
        """Callback function used by Tobii SDK.

        Args:
            gaze_data: gaze data provided by the eye tracker.

        Returns:
            None
        """
        self.gaze_data.append(gaze_data)

    def _get_psychopy_pos(self, p, units=None):
        """Convert Tobii ADCS coordinates to PsychoPy coordinates.

        Args:
            p: Gaze position (x, y) in Tobii ADCS.
            units: The PsychoPy coordinate system to use.

        Returns:
            Gaze position in PsychoPy coordinate systems. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (2 * p[0] - 1, -2 * p[1] + 1)
        elif units == "height":
            return ((p[0] - 0.5) * (self.win.size[0] / self.win.size[1]),
                    -p[1] + 0.5)
        elif units in ["pix", "cm", "deg", "degFlat", "degFlatPos"]:
            p_pix = self._tobii2pix(p)
            if units == "pix":
                return p_pix
            elif units == "cm":
                return tuple(pix2cm(pos, self.win.monitor) for pos in p_pix)
            elif units == "deg":
                tuple(pix2deg(pos, self.win.monitor) for pos in p_pix)
            else:
                return tuple(
                    pix2deg(np.array(p_pix),
                            self.win.monitor,
                            correctFlat=True))
        else:
            raise ValueError("unit ({}) is not supported.".format(units))

    def _get_tobii_pos(self, p, units=None):
        """Convert PsychoPy coordinates to Tobii ADCS coordinates.

        Args:
            p: Gaze position (x, y) in PsychoPy coordinate systems.
            units: The PsychoPy coordinate system of p.

        Returns:
            Gaze position in Tobii ADCS. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (p[0] / 2 + 0.5, p[1] / -2 + 0.5)
        elif units == "height":
            return (p[0] * (self.win.size[1] / self.win.size[0]) + 0.5,
                    -p[1] + 0.5)
        elif units == "pix":
            return self._pix2tobii(p)
        elif units in ["cm", "deg", "degFlat", "degFlatPos"]:
            if units == "cm":
                p_pix = (cm2pix(p[0], self.win.monitor),
                         cm2pix(p[1], self.win.monitor))
            elif units == "deg":
                p_pix = (
                    deg2pix(p[0], self.win.monitor),
                    deg2pix(p[1], self.win.monitor),
                )
            elif units in ["degFlat", "degFlatPos"]:
                p_pix = deg2pix(np.array(p),
                                self.win.monitor,
                                correctFlat=True)
            p_pix = tuple(round(pos, 0) for pos in p_pix)
            return self._pix2tobii(p_pix)
        else:
            raise ValueError("unit ({}) is not supported".format(units))

    def _pix2tobii(self, p):
        """Convert PsychoPy pixel coordinates to Tobii ADCS.

            Called by _get_tobii_pos.

        Args:
            p: Gaze position (x, y) in pixels.

        Returns:
            Gaze position in Tobii ADCS. For example: (0,0).
        """
        return (p[0] / self.win.size[0] + 0.5, -p[1] / self.win.size[1] + 0.5)

    def _tobii2pix(self, p):
        """Convert Tobii ADCS to PsychoPy pixel coordinates.

            Called by _get_psychopy_pos.

        Args:
            p: Gaze position (x, y) in Tobii ADCS.

        Returns:
            Gaze position in PsychoPy pixels coordinate system. For example:
            (0, 0).
        """
        return (round(self.win.size[0] * (p[0] - 0.5),
                      0), round(-self.win.size[1] * (p[1] - 0.5), 0))

    def _get_psychopy_pos_from_trackbox(self, p, units=None):
        """Convert Tobii TBCS coordinates to PsychoPy coordinates.

            Called by show_status.

        Args:
            p: Gaze position (x, y) in Tobii TBCS.
            units: The PsychoPy coordinate system to use.

        Returns:
            Gaze position in PsychoPy coordinate systems. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (-2 * p[0] + 1, -2 * p[1] + 1)
        elif units == "height":
            return ((-p[0] + 0.5) * (self.win.size[0] / self.win.size[1]),
                    -p[1] + 0.5)
        elif units in ["pix", "cm", "deg", "degFlat", "degFlatPos"]:
            p_pix = (
                round((-p[0] + 0.5) * self.win.size[0], 0),
                round((-p[1] + 0.5) * self.win.size[1], 0),
            )
            if units == "pix":
                return p_pix
            elif units == "cm":
                return tuple(pix2cm(pos, self.win.monitor) for pos in p_pix)
            elif units == "deg":
                return tuple(pix2deg(pos, self.win.monitor) for pos in p_pix)
            else:
                return tuple(
                    pix2deg(np.array(p_pix),
                            self.win.monitor,
                            correctFlat=True))
        else:
            raise ValueError("unit ({}) is not supported.".format(units))

    def _flush_to_file(self):
        """Write data to disk.

        Args:
            None

        Returns:
            None
        """
        self.datafile.flush()  # internal buffer to RAM
        os.fsync(self.datafile.fileno())  # RAM file cache to disk

    def _convert_tobii_record(self, record):
        """Convert tobii coordinates to output style.

        Args:
            record: raw gaze data

        Returns:
            reformed gaze data
        """
        lp = self._get_psychopy_pos(record["left_gaze_point_on_display_area"])
        rp = self._get_psychopy_pos(record["right_gaze_point_on_display_area"])

        # gaze
        if not (record["left_gaze_point_validity"]
                or record["right_gaze_point_validity"]):  # not detected
            ave = (np.nan, np.nan)
        elif not record["left_gaze_point_validity"]:
            ave = rp  # use right eye
        elif not record["right_gaze_point_validity"]:
            ave = lp  # use left eye
        else:
            ave = ((lp[0] + rp[0]) / 2.0, (lp[1] + rp[1]) / 2.0)

        # pupil
        if not (record["left_pupil_validity"]
                or record["right_pupil_validity"]):  # not detected
            pup = np.nan
        elif not record["left_pupil_validity"]:
            pup = record["right_pupil_diameter"]  # use right pupil
        elif not record["right_pupil_validity"]:
            pup = record["left_pupil_diameter"]  # use left pupil
        else:
            pup = (record["left_pupil_diameter"] +
                   record["right_pupil_diameter"]) / 2.0
        out = (
            round((record["system_time_stamp"] - self.t0) / 1000.0, 1),
            round(lp[0], 4),
            round(lp[1], 4),
            int(record["left_gaze_point_validity"]),
            round(rp[0], 4),
            round(rp[1], 4),
            int(record["right_gaze_point_validity"]),
            round(ave[0], 4),
            round(ave[1], 4),
            round(record["left_pupil_diameter"], 4),
            int(record["left_pupil_validity"]),
            round(record["right_pupil_diameter"], 4),
            int(record["right_pupil_validity"]),
            round(pup, 4))  # yapf: disable
        out = (str(x) for x in out)
        return out

    def _flush_data(self):
        """Wrapper for writing the header and data to the data file.

        Args:
            None

        Returns:
            None
        """
        if not self.gaze_data:
            raise RuntimeWarning("No data were collected.")

        if self.recording:
            raise RuntimeWarning(
                "Still recording. Data are only saved to the disk after "
                "stop_recording() is called to prevent large latency in the "
                "eye-tracking data.")

        self.datafile.write("Session Start\n")
        # write header
        self.datafile.write("\t".join([
            "TimeStamp",
            "GazePointXLeft",
            "GazePointYLeft",
            "ValidityLeft",
            "GazePointXRight",
            "GazePointYRight",
            "ValidityRight",
            "GazePointX",
            "GazePointY",
            "PupilSizeLeft",
            "PupilValidityLeft",
            "PupilSizeRight",
            "PupilValidityRight",
            "PupilSize"]) + "\n")  # yapf: disable
        self._flush_to_file()

        for gaze_data in self.gaze_data:
            output = self._convert_tobii_record(gaze_data)
            self.datafile.write("\t".join(output))
            self.datafile.write("\n")
        else:
            # write the events in the end of data
            for this_event in self.event_data:
                self.datafile.write("{}\t{}\n".format(*this_event))
        self.datafile.write("Session End\n")
        self._flush_to_file()

    def _collect_calibration_data(self, p):
        """Callback function used by Tobii calibration in run_calibration.

        Args:
            p: the calibration point

        Returns:
            None
        """
        self.calibration.collect_data(*self._get_tobii_pos(p))

    def _collect_validation_data(self, p):
        """Callback function used by Tobii Pro SDK addons."""
        self.validation.start_collecting_data(Point2(*self._get_tobii_pos(p)))
        # wait a bit for data collection
        while self.validation.is_collecting_data:
            core.wait(0.5, 0.0)

    def _open_datafile(self):
        """Open a file for gaze data.

        Args:
            None

        Returns:
            None
        """
        self.datafile = open(self.filename, "w")
        _write_buffer = "Recording date:\t{}\n".format(
            datetime.now().strftime("%Y/%m/%d"))
        _write_buffer += "Recording time:\t{}\n".format(
            datetime.now().strftime("%H:%M:%S"))
        _write_buffer += "Recording resolution:\t{} x {}\n".format(
            *self.win.size)
        _write_buffer += "PsychoPy units:\t{}\n".format(self.win.units)
        if self.validation_result_buffers is not None:
            _write_buffer += "\n".join(self.validation_result_buffers)
            self.validation_result_buffers = None

        self.datafile.write(_write_buffer)
        self._flush_to_file()

    def start_recording(self, filename=None, newfile=True):
        """Start recording

        Args:
            filename: the name of the data file. If None, use default name.
                Default is None.
            newfile: open a new file to save data. Default is True.

        Returns:
            None
        """
        if filename is not None:
            self.filename = filename

        if newfile:
            self._open_datafile()

        self.gaze_data = []
        self.event_data = []
        self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA,
                                     self._on_gaze_data,
                                     as_dictionary=True)
        core.wait(1)  # wait a bit for the eye tracker to get ready
        self.recording = True
        self.t0 = tr.get_system_time_stamp()

    def stop_recording(self):
        """Stop recording.

        Args:
            None

        Returns:
            None
        """
        if not self.recording:
            raise RuntimeWarning("Not recoding now.")

        self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA,
                                         self._on_gaze_data)
        self.recording = False
        # time correction for event data
        self.event_data = [(round((x[0] - self.t0) / 1000.0, 1), x[1])
                           for x in self.event_data]
        self._flush_data()

    def get_current_gaze_position(self):
        """Get the newest gaze position.

        Args:
            None

        Returns:
            A tuple of the newest gaze position in PsychoPy coordinate system.
            For example: (0, 0).
        """
        if not self.gaze_data:
            return (np.nan, np.nan)
        else:
            gaze_data = self.gaze_data[-1]
            lp = self._get_psychopy_pos(
                gaze_data["left_gaze_point_on_display_area"])
            rp = self._get_psychopy_pos(
                gaze_data["right_gaze_point_on_display_area"])
            if not (gaze_data["left_gaze_point_validity"]
                    or gaze_data["right_gaze_point_validity"]):  # not detected
                return (np.nan, np.nan)
            elif not gaze_data["left_gaze_point_validity"]:
                ave = rp  # use right eye
            elif not gaze_data["right_gaze_point_validity"]:
                ave = lp  # use left eye
            else:
                ave = ((lp[0] + rp[0]) / 2.0, (lp[1] + rp[1]) / 2.0)

            return tuple(round(pos, 4) for pos in ave)

    def get_current_pupil_size(self):
        """Get the newest pupil size.

        Args:
            None

        Returns:
            The newest pupil diameter (mm) reported by the eye-tracker.
            If both eyes are detected, return the average pupil size. If
            either of the eyes is detected, it will be returned.
            For example: 3.1542.
        """
        if not self.gaze_data:
            return np.nan
        else:
            gaze_data = self.gaze_data[-1]
            if not (gaze_data["left_pupil_validity"]
                    or gaze_data["right_pupil_validity"]):  # not detected
                pup = np.nan
            elif not gaze_data["left_pupil_validity"]:
                pup = gaze_data["right_pupil_diameter"]  # use right pupil
            elif not gaze_data["right_pupil_validity"]:
                pup = gaze_data["left_pupil_diameter"]  # use left pupil
            else:
                pup = ((gaze_data["left_pupil_diameter"] +
                        gaze_data["right_pupil_diameter"]) / 2.0)

            return round(pup, 4)

    def record_event(self, event):
        """Record events with timestamp.

            This method works only during recording.

        Args:
            event: the event

        Returns:
            None
        """
        if not self.recording:
            raise RuntimeWarning("Not recoding now.")

        self.event_data.append([tr.get_system_time_stamp(), event])

    def close(self):
        """Close the data file.

        Args:
            None

        Returns:
            None
        """
        # stop recording if not already
        if self.recording:
            self.stop_recording()
        if self.datafile is None:
            raise RuntimeWarning(
                "Data file is not found. Use start_recording() to record and "
                "save the data.")

        self.datafile.close()

    def run_calibration(self,
                        calibration_points,
                        focus_time=0.5,
                        decision_key="space",
                        result_msg_color="white"):
        """Run calibration

        Args:
            calibration_points: list of position of the calibration points.
            focus_time: the duration allowing the subject to focus in seconds.
                        Default is 0.5.
            decision_key: key to leave the procedure. Default is space.
            result_msg_color: Color to be used for calibration result text.
                Accepts any PsychoPy color specification. Default is white.

        Returns:
            bool: The status of calibration. True for success, False otherwise.
        """
        if self.eyetracker is None:
            raise ValueError("Eyetracker is not found.")

        if not (2 <= len(calibration_points) <= 9):
            raise ValueError(
                "The number of calibration points must be between 2 and 9.")

        else:
            self.numkey_dict = {
                k: v
                for k, v in self.numkey_dict.items()
                if v < len(calibration_points)
            }
        # prepare calibration stimuli
        self.calibration_target_dot = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_dot_color,
        )
        self.calibration_target_disc = visual.Circle(
            self.win,
            radius=self.calibration_disc_size,
            fillColor=self.calibration_disc_color,
            lineColor=self.calibration_disc_color,
        )
        self.retry_marker = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_disc_color,
            autoLog=False,
        )
        if self.win.units == "norm":  # fix oval
            self.calibration_target_dot.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
            self.calibration_target_disc.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
            self.retry_marker.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
        result_msg = visual.TextStim(
            self.win,
            pos=(0, -self.win.size[1] / 4),
            color=result_msg_color,
            units="pix",
            alignText="left",
            autoLog=False,
        )

        self.original_calibration_points = calibration_points[:]
        # set all points
        cp_num = len(self.original_calibration_points)
        self.retry_points = list(range(cp_num))

        in_calibration_loop = True
        event.clearEvents()

        self.calibration.enter_calibration_mode()
        while in_calibration_loop:
            self.calibration_points = [
                self.original_calibration_points[x] for x in self.retry_points
            ]

            # clear the display
            self.win.flip()
            self.update_calibration(_focus_time=focus_time)
            self.calibration_result = self.calibration.compute_and_apply()
            self.win.flip()

            result_img = self._show_calibration_result()
            result_msg.setText(
                "Accept/Retry: {k}\n"
                "Select/Deselect all points: 0\n"
                "Select/Deselect recalibration points: 1-{p} key\n"
                "Abort: esc".format(k=decision_key, p=cp_num))

            waitkey = True
            self.retry_points = []
            while waitkey:
                for key in event.getKeys():
                    if key in [decision_key, "escape"]:
                        waitkey = False
                    elif key in self.numkey_dict:
                        if self.numkey_dict[key] == -1:
                            if len(self.retry_points) == cp_num:
                                self.retry_points = []
                            else:
                                self.retry_points = list(range(cp_num))
                        else:
                            key_index = self.numkey_dict[key]
                            if key_index < cp_num:
                                if key_index in self.retry_points:
                                    self.retry_points.remove(key_index)
                                else:
                                    self.retry_points.append(key_index)

                result_img.draw()
                if len(self.retry_points) > 0:
                    for retry_p in self.retry_points:
                        self.retry_marker.setPos(
                            self.original_calibration_points[retry_p])
                        self.retry_marker.draw()

                result_msg.draw()
                self.win.flip()

            if key == decision_key:
                if len(self.retry_points) == 0:
                    retval = True
                    in_calibration_loop = False
                else:  # retry
                    for point_index in self.retry_points:
                        x, y = self._get_tobii_pos(
                            self.original_calibration_points[point_index])
                        self.calibration.discard_data(x, y)
            elif key == "escape":
                retval = False
                in_calibration_loop = False

        self.calibration.leave_calibration_mode()

        return retval

    def run_validation(self,
                       validation_points=None,
                       sample_count=30,
                       timeout=1,
                       focus_time=0.5,
                       decision_key="space",
                       show_results=False,
                       save_to_file=True,
                       result_msg_color="white"):
        """Run validation.

        tobii_research_addons is required for running validation. Validation
        procedure is only available after a successful calibration or an error
        will be raised.
        Args:
            validation_points: list of position of the validation points. If
                None, the calibration points are used. Default is None.
            sample_count: The number of samples to collect. Default is 30,
                minimum 10, maximum 3000.
            timeout: Timeout in seconds. Default is 1, minimum 0.1, maximum 3.
            focus_time: the duration allowing the subject to focus in seconds.
                        Default is 0.5.
            decision_key: key to leave the procedure. Default is space.
            show_results: Whether to show the validation result. Default is
                False.
            save_to_file: Whether to save the validation result to the data
                file. Default is True.
            result_msg_color: Color to be used for calibration result text.
                Accepts any PsychoPy color specification. Default is white.

        Returns:
            tobii_research_addons.ScreenBasedCalibrationValidation.CalibrationValidationResult
        """
        if self.update_validation is None:
            raise ModuleNotFoundError("tobii_research_addons is not found.")

        # setup the procedure
        self.validation = ScreenBasedCalibrationValidation(
            self.eyetracker, sample_count, int(1000 * timeout))

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
        self._show_validation_result(result_buffer, show_results, save_to_file,
                                     decision_key, result_msg_color)

        return validation_result

    def _process_validation_result(self, validation_result):
        """Process validation result"""
        result_buffer = "Validation time:\t{}\n".format(
            datetime.now().strftime("%H:%M:%S"))
        # accuracy
        result_buffer += "Mean accuracy (in degrees):\t"
        val = (round(this_eye, 4)
               for this_eye in (validation_result.average_accuracy_left,
                                validation_result.average_accuracy_right))
        result_buffer += "left={}\tright={}\n".format(*val)

        result_buffer += "Mean accuracy (in pixels):\t"
        val = (np.nan, np.nan)
        try:
            val = (deg2pix(validation_result.average_accuracy_left,
                           self.win.monitor),
                   deg2pix(validation_result.average_accuracy_right,
                           self.win.monitor))
            val = (round(this_eye, 4) for this_eye in val)
        except ValueError:
            pass
        result_buffer += "left={}\tright={}\n".format(*val)

        # RMS
        result_buffer += "Mean precision (RMS error, in degrees):\t"
        val = (round(this_eye, 4)
               for this_eye in (validation_result.average_precision_rms_left,
                                validation_result.average_precision_rms_right))
        result_buffer += "left={}\tright={}\n".format(*val)

        result_buffer += "Mean precision (RMS error, in pixels):\t"
        val = (np.nan, np.nan)
        try:
            val = (deg2pix(validation_result.average_precision_rms_left,
                           self.win.monitor),
                   deg2pix(validation_result.average_precision_rms_right,
                           self.win.monitor))
            val = (round(this_eye, 4) for this_eye in val)
        except ValueError:
            pass
        result_buffer += "left={}\tright={}\n".format(*val)

        return result_buffer

    def _show_validation_result(self, result_buffer, show_results,
                                save_to_file, decision_key, result_msg_color):
        if save_to_file:
            if self.validation_result_buffers is None:
                self.validation_result_buffers = list()
            self.validation_result_buffers.append(result_buffer)

        if show_results:
            result_msg = visual.TextStim(self.win,
                                         pos=(0, -self.win.size[1] / 4),
                                         color=result_msg_color,
                                         units="pix",
                                         alignText="left",
                                         wrapWidth=self.win.size[0] * 0.6,
                                         autoLog=False)
            result_msg.setText(result_buffer.replace("\t", " "))
            result_msg.draw()
            self.win.flip()

            waitkey = True
            while waitkey:
                for key in event.getKeys():
                    if key == decision_key:
                        waitkey = False
                        break

    def _update_validation_auto(self, validation_points, _focus_time=0.5):
        """Automatic validation procedure."""
        # start
        clock = core.Clock()
        for current_validation_point in validation_points:
            self.calibration_target_disc.setPos(current_validation_point)
            self.calibration_target_dot.setPos(current_validation_point)
            clock.reset()
            while True:
                t = clock.getTime() * self.shrink_speed
                self.calibration_target_disc.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_disc_size
                ])
                self.calibration_target_dot.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_dot_size
                ])
                self.calibration_target_disc.draw()
                self.calibration_target_dot.draw()
                if clock.getTime() >= self._shrink_sec:
                    core.wait(_focus_time, 0.0)
                    self._collect_validation_data(current_validation_point)
                    break

                self.win.flip()

    def _show_calibration_result(self):
        img = Image.new("RGBA", tuple(self.win.size))
        img_draw = ImageDraw.Draw(img)
        result_img = visual.SimpleImageStim(self.win, img, autoLog=False)
        img_draw.rectangle(((0, 0), tuple(self.win.size)), fill=(0, 0, 0, 0))
        if self.calibration_result.status == tr.CALIBRATION_STATUS_FAILURE:
            # computeCalibration failed.
            pass
        else:
            if len(self.calibration_result.calibration_points) == 0:
                pass
            else:

                for this_point in self.calibration_result.calibration_points:
                    p = this_point.position_on_display_area
                    for this_sample in this_point.calibration_samples:
                        lp = this_sample.left_eye.position_on_display_area
                        rp = this_sample.right_eye.position_on_display_area
                        if (this_sample.left_eye.validity ==
                                tr.VALIDITY_VALID_AND_USED):
                            img_draw.line(
                                (
                                    (p[0] * self.win.size[0],
                                     p[1] * self.win.size[1]),
                                    (
                                        lp[0] * self.win.size[0],
                                        lp[1] * self.win.size[1],
                                    ),
                                ),
                                fill=(0, 255, 0, 255),
                            )
                        if (this_sample.right_eye.validity ==
                                tr.VALIDITY_VALID_AND_USED):
                            img_draw.line(
                                (
                                    (p[0] * self.win.size[0],
                                     p[1] * self.win.size[1]),
                                    (
                                        rp[0] * self.win.size[0],
                                        rp[1] * self.win.size[1],
                                    ),
                                ),
                                fill=(255, 0, 0, 255),
                            )
                    img_draw.ellipse(
                        (
                            (p[0] * self.win.size[0] - 3,
                             p[1] * self.win.size[1] - 3),
                            (p[0] * self.win.size[0] + 3,
                             p[1] * self.win.size[1] + 3),
                        ),
                        outline=(0, 0, 0, 255),
                    )

        result_img.setImage(img)
        return result_img

    def _update_calibration_auto(self, _focus_time=0.5):
        """Automatic calibration procedure."""
        # start calibration
        event.clearEvents()
        clock = core.Clock()
        for point_idx in self.retry_points:
            this_pos = self.original_calibration_points[point_idx]
            self.calibration_target_disc.setPos(this_pos)
            self.calibration_target_dot.setPos(this_pos)
            clock.reset()
            while True:
                t = clock.getTime() * self.shrink_speed
                self.calibration_target_disc.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_disc_size
                ])
                self.calibration_target_dot.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_dot_size
                ])
                self.calibration_target_disc.draw()
                self.calibration_target_dot.draw()
                if clock.getTime() >= self._shrink_sec:
                    core.wait(_focus_time, 0.0)
                    self._collect_calibration_data(this_pos)
                    break

                self.win.flip()

    def show_status(self, decision_key="space"):
        """Showing the participant's gaze position in track box.

        Args:
            decision_key: key to leave the procedure. Default is space.

        Returns:
            None
        """
        bgrect = visual.Rect(self.win,
                             pos=(0, 0.4),
                             width=0.25,
                             height=0.2,
                             lineColor="white",
                             fillColor="black",
                             units="height",
                             autoLog=False)

        leye = visual.Circle(self.win,
                             size=0.02,
                             units="height",
                             lineColor=None,
                             fillColor="green",
                             autoLog=False)

        reye = visual.Circle(self.win,
                             size=0.02,
                             units="height",
                             lineColor=None,
                             fillColor="red",
                             autoLog=False)

        zbar = visual.Rect(self.win,
                           pos=(0, 0.28),
                           width=0.25,
                           height=0.03,
                           lineColor="green",
                           fillColor="green",
                           units="height",
                           autoLog=False)

        zc = visual.Rect(self.win,
                         pos=(0, 0.28),
                         width=0.01,
                         height=0.03,
                         lineColor="white",
                         fillColor="white",
                         units="height",
                         autoLog=False)

        zpos = visual.Rect(self.win,
                           pos=(0, 0.28),
                           width=0.005,
                           height=0.03,
                           lineColor="black",
                           fillColor="black",
                           units="height",
                           autoLog=False)

        if self.eyetracker is None:
            raise ValueError("Eyetracker is not found.")

        self.eyetracker.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE,
                                     self._on_gaze_data,
                                     as_dictionary=True)
        core.wait(1)  # wait a bit for the eye tracker to get ready

        b_show_status = True

        while b_show_status:
            bgrect.draw()
            zbar.draw()
            zc.draw()
            gaze_data = self.gaze_data[-1]
            lv = gaze_data["left_user_position_validity"]
            rv = gaze_data["right_user_position_validity"]
            lx, ly, lz = gaze_data["left_user_position"]
            rx, ry, rz = gaze_data["right_user_position"]
            if lv:
                lx, ly = self._get_psychopy_pos_from_trackbox([lx, ly],
                                                              units="height")
                leye.setPos((round(lx * 0.25, 4), round(ly * 0.2 + 0.4, 4)))
                leye.draw()
            if rv:
                rx, ry = self._get_psychopy_pos_from_trackbox([rx, ry],
                                                              units="height")
                reye.setPos((round(rx * 0.25, 4), round(ry * 0.2 + 0.4, 4)))
                reye.draw()
            if lv or rv:
                zpos.setPos((
                    round((((lz * int(lv) + rz * int(rv)) /
                            (int(lv) + int(rv))) - 0.5) * 0.125, 4),
                    0.28,
                ))
                zpos.draw()

            for key in event.getKeys():
                if key == decision_key:
                    b_show_status = False
                    break

            self.win.flip()

        self.eyetracker.unsubscribe_from(tr.EYETRACKER_USER_POSITION_GUIDE,
                                         self._on_gaze_data)

    # property getters and setters for parameter changes
    @property
    def shrink_speed(self):
        return self._shrink_speed

    @shrink_speed.setter
    def shrink_speed(self, value):
        self._shrink_speed = value
        # adjust the duration of shrinking
        self._shrink_sec = 3 / self._shrink_speed

    @property
    def shrink_sec(self):
        return self._shrink_sec

    @shrink_sec.setter
    def shrink_sec(self, value):
        self._shrink_sec = value


class TobiiInfantController(TobiiController):
    """Tobii controller with children-friendly calibration procedure.

        This is a subclass of TobiiController, with some modification for
        developmental research.

    Args:
        win: psychopy.visual.Window object.
        id: the id of eyetracker.
        filename: the name of the data file.

    Attributes:
        shrink_speed: the shrinking speed of target in calibration.
            Default is 1.
        numkey_dict: keys used for calibration. Default is the number pad.
    """
    def __init__(self, win, id=0, filename="gaze_TOBII_output.tsv"):
        super().__init__(win, id, filename)
        self.update_calibration = self._update_calibration_infant
        # slower for infants
        self.shrink_speed = 1
        if _has_addons:
            self.update_validation = self._update_validation_infant

    def _update_calibration_infant(self,
                                   _focus_time=0.5,
                                   collect_key="space",
                                   exit_key="return"):
        """The calibration procedure designed for infants.

            An implementation of run_calibration().

        Args:
            focus_time: the duration allowing the subject to focus in seconds.
                            Default is 0.5.
            collect_key: key to start collecting samples. Default is space.
            exit_key: key to finish and leave the current calibration
                procedure. It should not be confused with `decision_key`, which
                is used to leave the whole calibration process. `exit_key` is
                used to leave the current calibration, the user may recalibrate
                or accept the result afterwards. Default is return (Enter)

        Returns:
            None
        """
        # start calibration
        event.clearEvents()
        point_idx = -1
        in_calibration = True
        clock = core.Clock()
        while in_calibration:
            # get keys
            keys = event.getKeys()
            for key in keys:
                if key in self.numkey_dict:
                    point_idx = self.numkey_dict[key]

                    # play the sound if it exists
                    if self._audio is not None:
                        if point_idx in self.retry_points:
                            self._audio.play()
                elif key == collect_key:
                    # allow the participant to focus
                    core.wait(_focus_time, 0.0)
                    # collect samples when space is pressed
                    if point_idx in self.retry_points:
                        self._collect_calibration_data(
                            self.original_calibration_points[point_idx])
                        point_idx = -1
                        # stop the sound
                        if self._audio is not None:
                            self._audio.pause()
                elif key == exit_key:
                    # exit calibration when return is pressed
                    in_calibration = False
                    break

            # draw calibration target
            if point_idx in self.retry_points:
                this_target = self.targets.get_stim(point_idx)
                this_pos = self.original_calibration_points[point_idx]
                this_target.setPos(this_pos)
                t = clock.getTime() * self.shrink_speed
                newsize = [
                    (np.sin(t)**2 + self.calibration_target_min) * e
                    for e in self.targets.get_stim_original_size(point_idx)
                ]
                this_target.setSize(newsize)
                this_target.draw()
            self.win.flip()

    def _update_validation_infant(self,
                                  validation_points,
                                  _focus_time=0.5,
                                  collect_key="space"):
        """Semi-automatic validation procedure for infants."""
        for idx, current_validation_point in enumerate(validation_points):
            event.clearEvents()
            deg = 0
            this_target = self.targets.get_stim(idx)
            orig_size = self.targets.get_stim_original_size(idx)
            this_target.setSize(
                (self.calibration_disc_size,
                 self.calibration_disc_size * (orig_size[0] / orig_size[1])))
            this_target.setPos(current_validation_point)
            in_validation = True
            while in_validation:
                deg += 0.5
                this_target.setOri(ceil(deg))
                this_target.draw()
                self.win.flip()

                keys = event.getKeys()
                for key in keys:
                    if key == collect_key:
                        core.wait(_focus_time, 0.0)
                        self._collect_validation_data(current_validation_point)
                        in_validation = False
                        break

    def run_calibration(self,
                        calibration_points,
                        infant_stims,
                        shuffle=True,
                        audio=None,
                        focus_time=0.5,
                        decision_key="space",
                        result_msg_color="white",
                        *kwargs):
        """Run calibration.

            How to use:
                - Press 1-9 to present calibration stimulus (press 0 to hide
                  it).
                - Press space to start collect calibration samples.
                - Press Enter to finish the calibration and show the
                  calibration result.
                - Choose the points to recalibrate with 1-9. If no points are
                  selected, the calibration result will be accepted and
                  applied.
                - Press decision_key (default is space) to accept the
                  calibration result or recalibrate.

            The experimenter should manually show the stimulus and collect data
            when the subject is paying attention to the stimulus.

        Args:
            calibration_points: list of position of the calibration points.
            infant_stims: list of images to attract the infant. If the number
                of images is equal to or larger than the number of calibration
                points, the images will be used in order. If not, the images
                will be repeated.
            shuffle: whether to shuffle the presentation order of the stimuli.
                Default is True.
            audio: the psychopy.sound.Sound object to play during calibration.
                If None, no sound will be played. Default is None.
            focus_time: the duration allowing the subject to focus in seconds.
                        Default is 0.5.
            decision_key: key to leave the procedure. Default is space.
            result_msg_color: Color to be used for calibration result text.
                Accepts any PsychoPy color specification. Default is white.
            *kwargs: other arguments to pass into psychopy.visual.ImageStim.
        Returns:
            bool: The status of calibration. True for success, False otherwise.
        """
        if self.eyetracker is None:
            raise ValueError("Eyetracker is not found.")

        if not (2 <= len(calibration_points) <= 9):
            raise ValueError("Calibration points must be between 2 and 9")

        else:
            self.numkey_dict = {
                k: v
                for k, v in self.numkey_dict.items()
                if v < len(calibration_points)
            }

        # prepare calibration stimuli
        self.targets = InfantStimuli(self.win,
                                     infant_stims,
                                     shuffle=shuffle,
                                     *kwargs)
        self._audio = audio

        self.retry_marker = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_disc_color,
            autoLog=False,
        )
        if self.win.units == "norm":  # fix oval
            self.retry_marker.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
        result_msg = visual.TextStim(
            self.win,
            pos=(0, -self.win.size[1] / 4),
            color=result_msg_color,
            units="pix",
            autoLog=False,
        )

        self.calibration.enter_calibration_mode()

        self.original_calibration_points = calibration_points[:]
        # set all points
        cp_num = len(self.original_calibration_points)
        self.retry_points = list(range(cp_num))

        in_calibration_loop = True
        event.clearEvents()
        while in_calibration_loop:
            self.calibration_points = [
                self.original_calibration_points[x] for x in self.retry_points
            ]

            # clear the display
            self.win.flip()
            self.update_calibration(_focus_time=focus_time)
            self.calibration_result = self.calibration.compute_and_apply()
            self.win.flip()

            result_img = self._show_calibration_result()
            result_msg.setText(
                "Accept/Retry: {k}\n"
                "Select/Deselect all points: 0\n"
                "Select/Deselect recalibration points: 1-{p} key\n"
                "Abort: esc".format(k=decision_key, p=cp_num))

            waitkey = True
            self.retry_points = []
            while waitkey:
                for key in event.getKeys():
                    if key in [decision_key, "escape"]:
                        waitkey = False
                    elif key in self.numkey_dict:
                        if self.numkey_dict[key] == -1:
                            if len(self.retry_points) == cp_num:
                                self.retry_points = []
                            else:
                                self.retry_points = list(range(cp_num))
                        else:
                            key_index = self.numkey_dict[key]
                            if key_index < cp_num:
                                if key_index in self.retry_points:
                                    self.retry_points.remove(key_index)
                                else:
                                    self.retry_points.append(key_index)

                result_img.draw()
                if len(self.retry_points) > 0:
                    for retry_p in self.retry_points:
                        self.retry_marker.setPos(
                            self.original_calibration_points[retry_p])
                        self.retry_marker.draw()

                result_msg.draw()
                self.win.flip()

            if key == decision_key:
                if len(self.retry_points) == 0:
                    retval = True
                    in_calibration_loop = False
                else:  # retry
                    for point_index in self.retry_points:
                        x, y = self._get_tobii_pos(
                            self.original_calibration_points[point_index])
                        self.calibration.discard_data(x, y)
            elif key == "escape":
                retval = False
                in_calibration_loop = False

        self.calibration.leave_calibration_mode()

        return retval

    def run_validation(self,
                       validation_points=None,
                       infant_stims=None,
                       shuffle=True,
                       sample_count=30,
                       timeout=1,
                       focus_time=0.5,
                       decision_key="space",
                       show_results=False,
                       save_to_file=True,
                       result_msg_color="white",
                       *kwargs):
        """Run validation.
        Press space to start collect valdiation samples.

        Args:
            validation_points: list of position of the validation points. If
                None, the calibration points are used. Default is None.
            infant_stims: list of images to attract the infant. If None,
                stimuli used in the latest calibration procedure are used.
                Default is None.
            shuffle: whether to shuffle the presentation order of the stimuli.
                Default is True. Has no effects if infant_stims is set to None.
            sample_count: The number of samples to collect. Default is 30,
                minimum 10, maximum 3000.
            timeout: Timeout in seconds. Default is 1, minimum 0.1, maximum 3.
            focus_time: the duration allowing the subject to focus in seconds.
                        Default is 0.5.
            decision_key: key to leave the procedure. Default is space.
            show_results: Whether to show the validation result. Default is
                False.
            save_to_file: Whether to save the validation result to the data
                file. Default is True.
            result_msg_color: Color to be used for calibration result text.
                Accepts any PsychoPy color specification. Default is white.
            *kwargs: other arguments to pass into psychopy.visual.ImageStim.
                Has no effects if infant_stims is set to None.
        Returns:
            tobii_research_addons.ScreenBasedCalibrationValidation.CalibrationValidationResult
        """
        if self.update_validation is None:
            raise ModuleNotFoundError("tobii_research_addons is not found.")

        # setup the procedure
        self.validation = ScreenBasedCalibrationValidation(
            self.eyetracker, sample_count, int(1000 * timeout))

        if validation_points is None:
            validation_points = self.original_calibration_points

        if infant_stims is not None:
            self.targets = InfantStimuli(self.win,
                                         infant_stims,
                                         shuffle=shuffle,
                                         *kwargs)

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
        self._show_validation_result(result_buffer, show_results, save_to_file,
                                     decision_key, result_msg_color)

        return validation_result

    # Collect looking time
    def collect_lt(self, max_time, min_away, blink_dur=1):
        """Collect looking time data in runtime.

            Collect and calculate looking time in runtime. Also end the trial
            automatically when the participant look away.

        Args:
            max_time: maximum looking time in seconds.
            min_away: minimum duration to stop in seconds.
            blink_dur: the tolerable duration of missing data in seconds.

        Returns:
            lt (float): The looking time in the trial.
        """
        trial_timer = core.Clock()
        absence_timer = core.Clock()
        away_time = []

        looking = True
        trial_timer.reset()
        absence_timer.reset()

        while trial_timer.getTime() <= max_time:
            gaze_data = self.gaze_data[-1]
            lv = gaze_data["left_gaze_point_validity"]
            rv = gaze_data["right_gaze_point_validity"]

            if any((lv, rv)):
                # if the last sample is missing
                if not looking:
                    away_dur = absence_timer.getTime()
                    if away_dur >= min_away:
                        away_time.append(away_dur)
                        lt = trial_timer.getTime() - np.sum(away_time)
                        # stop the trial
                        return round(lt, 3)
                    elif away_dur >= blink_dur:
                        away_time.append(away_dur)
                    # if missing samples are tolerable
                    else:
                        pass
                looking = True
                absence_timer.reset()
            else:
                if absence_timer.getTime() >= min_away:
                    away_dur = absence_timer.getTime()
                    away_time.append(away_dur)
                    lt = trial_timer.getTime() - np.sum(away_time)
                    # terminate the trial
                    return round(lt, 3)
                else:
                    pass
                looking = False

            self.win.flip()
        # if the loop is completed, return the looking time
        else:
            lt = max_time - np.sum(away_time)
            return round(lt, 3)


# backward compatible
tobii_controller = TobiiController
tobii_infant_controller = TobiiInfantController
