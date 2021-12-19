import pya
from pya import DPoint, DPath, Path, Polygon, Point, Text, Trans, Application, LayoutMetaInfo
import numpy as np

from SiEPIC.utils import get_technology_by_name


class SWG_WDM(pya.PCellDeclarationHelper):
    """
    The PCell declaration for SWG-based WDM Coupler for 1310 nm and 1550 nm.
    """

    def __init__(self):
        # Important: initialize the super class
        super(SWG_WDM, self).__init__()
        TECHNOLOGY = get_technology_by_name('EBeam')

        # declare the parameters
        # self.param("length", self.TypeDouble, "Waveguide length", default = 10.0)
        self.param("wi", self.TypeDouble, "Width of Input Waveguide", default = 0.5)
        self.param("Lc", self.TypeDouble, "Length of the Coupler", default = 34.4)
        self.param("a", self.TypeDouble, "SWG Period Length (Lambda*DC)", default = 0.082)
        self.param("g", self.TypeDouble, "Coupler Gap", default = 0.100)
        self.param("Lambda", self.TypeDouble, "Lambda (SWG Period)", default = 0.2)
        self.param("Lt", self.TypeDouble, "Length of Tapers", default = 5.0)
        self.param("wt", self.TypeDouble, "Width at the end of the taper", default = 0.06)
        self.param("Lb", self.TypeDouble, "Length of S-Bends", default = 10.0)
        self.param("Dy", self.TypeDouble, "S-bend vertical offset", default = 4.0)
        self.param("ws", self.TypeDouble, "Width of the Coupler SWG", default = 1.0)

        self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        # fetching parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        wi = self.wi/dbu
        Lc = round(self.Lc/self.Lambda)*self.Lambda/dbu
        Lt = round(self.Lt/self.Lambda)*self.Lambda/dbu
        wt = self.wt/dbu
        Lb = self.Lb/dbu
        Dy = self.Dy/2/dbu
        ws = self.ws/dbu
        Lambda = self.Lambda/dbu
        a = self.a/dbu
        g = self.g/dbu

        from SiEPIC.utils import arc_wg_xy
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):

        # Input Taper
        # Triangle
        x0, y0 = -Lc/2 - Lt/2, -g/2 - ws/2
        pts = [
            Point(x0 - Lt/2, y0 - wi/2),
            Point(x0 - Lt/2, y0 + wi/2),
            Point(x0 + Lt/2, y0 + wt/2),
            Point(x0 + Lt/2, y0 - wt/2)]
        shapes(LayerSiN).insert(Polygon(pts))
        # SWG
        x0, y0 = -Lc/2 - Lt/2, -g/2 - ws/2
        theta_t = np.arctan((ws-wi)/Lt)
        for i in range(0, round(Lt/Lambda)):
            pts = [
                Point(x0 - Lt/2 + i*Lambda, y0 - (wi + np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda, y0 + (wi + np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 + (wi + np.sin(theta_t)*(i*Lambda + a))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 - (wi + np.sin(theta_t)*(i*Lambda + a))/2)]
            shapes(LayerSiN).insert(Polygon(pts))

        # SWG Coupler
        x0, y0 = 0, 0
        for i in range(0, round(Lc/Lambda)):
            box1 = Box(x0 - Lc/2 + i*Lambda, y0 - g/2,
                x0 - Lc/2 + i*Lambda + a, y0 - (g/2 + ws))
            box2 = Box(x0 - Lc/2 + i*Lambda, y0 + g/2,
                x0 - Lc/2 + i*Lambda + a, y0 + g/2 + ws)
            shapes(LayerSiN).insert(box1)
            shapes(LayerSiN).insert(box2)

        # Output Taper 1
        # Triangle
        x0, y0 = Lc/2 + Lt/2, -g/2 - ws/2
        pts = [
            Point(x0 - Lt/2, y0 - wt/2),
            Point(x0 - Lt/2, y0 + wt/2),
            Point(x0 + Lt/2, y0 + wi/2),
            Point(x0 + Lt/2, y0 - wi/2)]
        shapes(LayerSiN).insert(Polygon(pts))
        # SWG
        theta_t = np.arctan((ws-wi)/Lt)
        for i in range(0, round(Lt/Lambda)):
            pts = [
                Point(x0 - Lt/2 + i*Lambda, y0 - (ws - np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda, y0 + (ws - np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 + (ws - np.sin(theta_t)*(i*Lambda + a))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 - (ws - np.sin(theta_t)*(i*Lambda + a))/2)]
            shapes(LayerSiN).insert(Polygon(pts))

        # Output Taper 2
        # Triangle
        x0, y0 = Lc/2 + Lt/2, g/2 + ws/2
        pts = [
            Point(x0 - Lt/2, y0 - wt/2),
            Point(x0 - Lt/2, y0 + wt/2),
            Point(x0 + Lt/2, y0 + wi/2),
            Point(x0 + Lt/2, y0 - wi/2)]
        shapes(LayerSiN).insert(Polygon(pts))
        # SWG
        theta_t = np.arctan((ws-wi)/Lt)
        for i in range(0, round(Lt/Lambda)):
            pts = [
                Point(x0 - Lt/2 + i*Lambda, y0 - (ws - np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda, y0 + (ws - np.sin(theta_t)*(i*Lambda))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 + (ws - np.sin(theta_t)*(i*Lambda + a))/2),
                Point(x0 - Lt/2 + i*Lambda + a, y0 - (ws - np.sin(theta_t)*(i*Lambda + a))/2)]
            shapes(LayerSiN).insert(Polygon(pts))

        # S-bends
        x0, y0 = Lc/2 + Lt, g/2 + ws/2
        Dx = Lb/2
        yc = y0 + Dx**2/2/Dy + Dy/2
        R = yc - y0
        theta = np.arctan(Dx/(R-Dy))*180/np.pi
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):
        arc1 = pya.Polygon(arc_wg_xy(
            x0, yc, R, wi, -90, -90 + theta))
        arc2 = pya.Polygon(arc_wg_xy(
            x0 + Lb, y0 + 2*Dy - R, R, wi, 90, 90 + theta))
        shapes(LayerSiN).insert(arc1)
        shapes(LayerSiN).insert(arc2)

        x0, y0 = Lc/2 + Lt, -g/2 - ws/2
        arc1 = pya.Polygon(arc_wg_xy(
            x0, y0 - R, R, wi, 90 - theta, 90))
        arc2 = pya.Polygon(arc_wg_xy(
            x0 + Lb, y0 - 2*Dy + R, R, wi, -90 - theta, -90))
        shapes(LayerSiN).insert(arc1)
        shapes(LayerSiN).insert(arc2)

        shapes(LayerPinRecN).insert(pya.Text(
            "opt1", pya.Trans(pya.Trans.R0, -Lc/2 - Lt, -g/2 - ws/2)
        )).text_size = 0.5/dbu
        shapes(LayerPinRecN).insert(pya.Text(
            "opt2", pya.Trans(pya.Trans.R0, Lc/2 + Lt + Lb, g/2 + ws/2 + 2*Dy)
        )).text_size = 0.5/dbu
        shapes(LayerPinRecN).insert(pya.Text(
            "opt3", pya.Trans(pya.Trans.R0, Lc/2 + Lt + Lb, -(g/2 + ws/2 + 2*Dy))
        )).text_size = 0.5/dbu


class Bruno_EBeam_Library(pya.Library):
    """
    The library where we will put the PCell into
    """

    def __init__(self):

        # Set the description
        self.description = "Bruno_EBeam_Library"

        # Create the PCell declarations

        self.layout().register_pcell("SWG_WDM", SWG_WDM())
        # That would be the place to put in more PCells ...
        # Register us with the name "MyLib".
        # If a library with that name already existed, it will be replaced then.
        self.register("Bruno_EBeam_Library")

# Instantiate and register the library
Bruno_EBeam_Library()
