from psychopy import monitors, visual
from psychopy_tobii_infant import TobiiController


class DummyController(TobiiController):
    def __init__(self, win):
        self.win = win


class TestCoord:
    """Test the transformation of coordinates."""
    def setup(self):
        self.mon = monitors.Monitor("dummy",
                                    width=12.8,
                                    distance=65,
                                    autoLog=False)
        self.win = visual.Window(size=[128, 128],
                                 units="pix",
                                 monitor=self.mon,
                                 fullscr=False,
                                 allowGUI=False,
                                 autoLog=False)

        self.controller = DummyController(self.win)

        self.tobii_points = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)]
        self.psy_points = {
            "norm": [(-1, 1), (1, 1), (1, -1), (-1, -1), (0, 0)],
            "height": [(-0.5, 0.5), (0.5, 0.5), (0.5, -0.5), (-0.5, -0.5),
                       (0, 0)],
            "pix": [(-64, 64), (64, 64), (64, -64), (-64, -64), (0, 0)]
        }

    def test_get_psychopy_pos_norm(self):
        trans_points = [
            self.controller._get_psychopy_pos(point, units="norm")
            for point in self.tobii_points
        ]
        psy_points = self.psy_points["norm"]
        for trans_point, psy_point in zip(trans_points, psy_points):
            trans_point = tuple(round(pos, 4) for pos in trans_point)
            assert trans_point == psy_point

    def test_get_psychopy_pos_height(self):
        trans_points = [
            self.controller._get_psychopy_pos(point, units="height")
            for point in self.tobii_points
        ]
        psy_points = self.psy_points["height"]
        for trans_point, psy_point in zip(trans_points, psy_points):
            trans_point = tuple(round(pos, 4) for pos in trans_point)
            assert trans_point == psy_point

    def test_get_tobii_pos_norm(self):
        psy_points = self.psy_points["norm"]
        trans_points = [
            self.controller._get_tobii_pos(point, units="norm")
            for point in psy_points
        ]
        for trans_point, tobii_point in zip(trans_points, self.tobii_points):
            trans_point = tuple(round(pos, 4) for pos in trans_point)
            assert trans_point == tobii_point

    def test_get_tobii_pos_height(self):
        psy_points = self.psy_points["height"]
        trans_points = [
            self.controller._get_tobii_pos(point, units="height")
            for point in psy_points
        ]
        for trans_point, tobii_point in zip(trans_points, self.tobii_points):
            trans_point = tuple(round(pos, 4) for pos in trans_point)
            assert trans_point == tobii_point

    def test_pix2tobii(self):
        psy_points = self.psy_points["pix"]
        trans_points = [
            self.controller._pix2tobii(point) for point in psy_points
        ]
        for trans_point, tobii_point in zip(trans_points, self.tobii_points):
            trans_point = tuple(round(pos, 4) for pos in trans_point)
            assert trans_point == tobii_point

    def test_tobii2pix(self):
        trans_points = [
            self.controller._tobii2pix(point) for point in self.tobii_points
        ]
        psy_points = self.psy_points["pix"]
        for trans_point, psy_point in zip(trans_points, psy_points):
            trans_point = tuple(round(pos, 0) for pos in trans_point)
            assert trans_point == psy_point
