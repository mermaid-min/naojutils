import numpy as np

class CS_FOV:
    def __init__(self, canvas, pt):
        self.canvas = canvas
        self.dc = canvas.dc if hasattr(canvas, 'dc') else canvas.get_draw_classes()
        self.pt_ctr = pt
        self.pa_rot_deg = 0.0
        self.flip_tf = False

    def set_pos(self, pt):
        self.pt_ctr = pt

    def set_pa(self, pa_deg):
        self.pa_rot_deg = pa_deg

    def flip_x(self, obj, xcenter):
        for o in obj.objects:
            if hasattr(o, 'flip_x'):
                o.flip_x(xcenter)

    def remove(self):
        for group in ['fov_base', 'det1_group', 'det2_group']:
            if hasattr(self, group) and getattr(self, group):
                try:
                    self.canvas.delete_object(getattr(self, group))
                except Exception as e:
                    print(f"Error removing {group}: {e}")
            setattr(self, group, None)


class MOIRCS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)
        self.moircs_fov = (0.0666667, 0.116667)  # Reference 4x7 arcmin in degrees
        self.circle_radius_deg = 0.05  # 3 arcmin diameter = 1.5 arcmin radius
        self.pixscale = 0.117 / 3600  # 0.117 arcsec/pixel converted to degrees/pixel
        self.text_off = 1.0
        self.fov_base = None
        self.det1_group = None
        self.det2_group = None
        self._build()

    def _build(self):
        x, y = self.pt_ctr
        # Square dimensions: 4x4 arcmin for each detector
        square_size = 0.0666667  # 4 arcmin in degrees
        xr = square_size * 0.5 / self.pixscale  # Half of 4 arcmin / pixscale
        yr = square_size * 0.5 / self.pixscale  # Half of 4 arcmin / pixscale
        radius_pixels = self.circle_radius_deg / self.pixscale  # 1.5 arcmin / pixscale
        # Offset centers to create 4x1 arcmin overlap
        offset = (square_size - 0.0166667) / 2 / self.pixscale  # Half of (4-1)/2 arcmin

        dc = self.dc

        # FOV circle, label, and center line (always created, visibility managed by show_fov_overlay)
        fov_circle = dc.Circle(x, y, radius_pixels, color='white', linewidth=1, fill=False)
        fov_label = dc.Text(
            x - xr, y + yr + offset, text="MOIRCS FOV (4x7 arcmin)", color='white', bgcolor='black', bgalpha=1.0
        )
        center_line = dc.Line(
            x - xr, y, x + xr, y, color='yellow', linewidth=1
        )
        self.fov_base = dc.CompoundObject(fov_circle, fov_label, center_line)
        self.canvas.add(self.fov_base)

        # Detector 1: 3 solid lines + 1 dashed line (top edge)
        det1_bottom = dc.Line(x - xr, y - offset - yr, x + xr, y - offset - yr, color='yellow', linewidth=1)
        det1_left = dc.Line(x - xr, y - offset - yr, x - xr, y - offset + yr, color='yellow', linewidth=1)
        det1_right = dc.Line(x + xr, y - offset - yr, x + xr, y - offset + yr, color='yellow', linewidth=1)
        det1_top = dc.Line(x - xr, y - offset + yr, x + xr, y - offset + yr, color='yellow', linewidth=1, linestyle='dash')
        label1 = dc.Text(
            x + xr, y - offset - (yr * self.text_off), text='Det 1', color='white', bgcolor='black', bgalpha=1.0
        )
        self.det1_group = dc.CompoundObject(det1_bottom, det1_left, det1_right, det1_top, label1)

        # Detector 2: 3 solid lines + 1 dashed line (bottom edge)
        det2_top = dc.Line(x - xr, y + offset + yr, x + xr, y + offset + yr, color='yellow', linewidth=1)
        det2_left = dc.Line(x - xr, y + offset - yr, x - xr, y + offset + yr, color='yellow', linewidth=1)
        det2_right = dc.Line(x + xr, y + offset - yr, x + xr, y + offset + yr, color='yellow', linewidth=1)
        det2_bottom = dc.Line(x - xr, y + offset - yr, x + xr, y + offset - yr, color='yellow', linewidth=1, linestyle='dash')
        label2 = dc.Text(
            x + xr, y + offset + (yr * self.text_off), text='Det 2', color='white', bgcolor='black', bgalpha=1.0
        )
        self.det2_group = dc.CompoundObject(det2_top, det2_left, det2_right, det2_bottom, label2)

    def __update(self):
        if not (self.fov_base or self.det1_group or self.det2_group):
            print("FOV overlay groups have been removed; skipping update.")
            return

        x, y = self.pt_ctr[:2]
        square_size = 0.0666667  # 4 arcmin in degrees
        xr = square_size * 0.5 / self.pixscale
        yr = square_size * 0.5 / self.pixscale
        radius_pixels = self.circle_radius_deg / self.pixscale
        offset = (square_size - 0.0166667) / 2 / self.pixscale  # Half of (4-1)/2 arcmin

        # Update fov_base (always present)
        if self.fov_base:
            self.fov_base.objects[0].x = x
            self.fov_base.objects[0].y = y
            self.fov_base.objects[0].radius = radius_pixels  # Circle
            self.fov_base.objects[1].x, self.fov_base.objects[1].y = x - xr, y + yr + offset  # FOV label
            self.fov_base.objects[2].x1, self.fov_base.objects[2].y1 = x - xr, y  # Center line
            self.fov_base.objects[2].x2, self.fov_base.objects[2].y2 = x + xr, y
            self.fov_base.objects[1].rot_deg = self.fov_base.objects[2].rot_deg = self.pa_rot_deg
            if self.flip_tf:
                self.flip_x(self.fov_base, x)
            if self.pa_rot_deg != 0:
                self.fov_base.rotate_deg([self.pa_rot_deg], [x, y])

        # Update det1_group (if present)
        if self.det1_group:
            self.det1_group.objects[0].x1, self.det1_group.objects[0].y1 = x - xr, y - offset - yr  # Bottom
            self.det1_group.objects[0].x2, self.det1_group.objects[0].y2 = x + xr, y - offset - yr
            self.det1_group.objects[1].x1, self.det1_group.objects[1].y1 = x - xr, y - offset - yr  # Left
            self.det1_group.objects[1].x2, self.det1_group.objects[1].y2 = x - xr, y - offset + yr
            self.det1_group.objects[2].x1, self.det1_group.objects[2].y1 = x + xr, y - offset - yr  # Right
            self.det1_group.objects[2].x2, self.det1_group.objects[2].y2 = x + xr, y - offset + yr
            self.det1_group.objects[3].x1, self.det1_group.objects[3].y1 = x - xr, y - offset + yr  # Top (dashed)
            self.det1_group.objects[3].x2, self.det1_group.objects[3].y2 = x + xr, y - offset + yr
            self.det1_group.objects[4].x, self.det1_group.objects[4].y = x + xr, y - offset - (yr * self.text_off)  # Label1
            self.det1_group.objects[4].rot_deg = self.pa_rot_deg
            if self.flip_tf:
                self.flip_x(self.det1_group, x)
            if self.pa_rot_deg != 0:
                self.det1_group.rotate_deg([self.pa_rot_deg], [x, y])

        # Update det2_group (if present)
        if self.det2_group:
            self.det2_group.objects[0].x1, self.det2_group.objects[0].y1 = x - xr, y + offset + yr  # Top
            self.det2_group.objects[0].x2, self.det2_group.objects[0].y2 = x + xr, y + offset + yr
            self.det2_group.objects[1].x1, self.det2_group.objects[1].y1 = x - xr, y + offset - yr  # Left
            self.det2_group.objects[1].x2, self.det2_group.objects[1].y2 = x - xr, y + offset + yr
            self.det2_group.objects[2].x1, self.det2_group.objects[2].y1 = x + xr, y + offset - yr  # Right
            self.det2_group.objects[2].x2, self.det2_group.objects[2].y2 = x + xr, y + offset + yr
            self.det2_group.objects[3].x1, self.det2_group.objects[3].y1 = x - xr, y + offset - yr  # Bottom (dashed)
            self.det2_group.objects[3].x2, self.det2_group.objects[3].y2 = x + xr, y + offset - yr
            self.det2_group.objects[4].x, self.det2_group.objects[4].y = x + xr, y + offset + (yr * self.text_off)  # Label2
            self.det2_group.objects[4].rot_deg = self.pa_rot_deg
            if self.flip_tf:
                self.flip_x(self.det2_group, x)
            if self.pa_rot_deg != 0:
                self.det2_group.rotate_deg([self.pa_rot_deg], [x, y])

    def set_pos(self, pt):
        super().set_pos(pt)
        self.__update()

    def set_pa(self, pa_deg):
        super().set_pa(pa_deg)
        self.__update()

    def scale_to_image(self, img_width, img_height):
        print(f"Image dimensions: width={img_width}, height={img_height}; using fixed pixel scale {self.pixscale*3600:.3f} arcsec/pixel")
        self.__update()

    def rebuild(self):
        self.remove()
        self._build()
        self.__update()