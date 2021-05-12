#!/usr/bin/python

# NOTES:
# The colorspace is _actually_ BGR, but assuming RGB is more fun
#   - https://gitlab.gnome.org/GNOME/gdk-pixbuf/-/issues/188

# TODO: 
# Add ability to switch colorspaces (see issue above)
# allow for multiple effects
# come up with new name
# make it so that all *.sh helper scripts set an appropiate termminal title (see cn)
# Optimize?
#   - see qutebrowser session: webcam glitch
# In principle, its possible to read an array of effects from a toml file, 
# and use those to create the tabs of an effects window

import sys, os, argparse, threading, warnings, toml

# make these optional
from sty import ef, rs

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Gio

from effects import available_effects
import const

def screen_size():
     import re
     from subprocess import run, PIPE
     
     output = run(['xrandr'], stdout=PIPE).stdout.decode()
     result = re.search(r'current (\d+) x (\d+)', output)
     return map(int, result.groups()) if result else (800, 600)

class PictureWindow(Gtk.Window):
     def __init__(self, app):
          Gtk.Window.__init__(self, title=" Output", application=app)
          self.set_wmclass("GLITCH", "GLITCH")
          self.set_default_size(const.WIDTH, const.HEIGHT)
          # self.set_border_width(10)

          w, h = screen_size()
          self.move(w*0.1, h*0.03)
          self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 1.0))

          self.im = Gtk.Image()
          self.add(self.im)

     def update_image(self, pixbuf):
          # also flipping seems to much of a slowdown
          self.im.set_from_pixbuf(pixbuf)
          # ___ resize ___
          # allocation = self.get_allocation()
          # w = allocation.width
          # h = allocation.height
          # s = w * 3

          # pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(im, GdkPixbuf.Colorspace.RGB, False, 8, 1280, 720, 3840)
          # pixbuf = pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)

          # self.im.set_from_pixbuf(pixbuf)


class SliderWindow(Gtk.ApplicationWindow):
     def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, title=" Effects", application=app)
        self.set_wmclass("GLITCH", "GLITCH")
        self.set_default_size(720, 420)
        
        self.connect("key-press-event",self._key_press_event)
        # hb = Gtk.HeaderBar()
        # hb.set_show_close_button(True)
        # hb.props.title = " Effects"
        # self.set_titlebar(hb)

        w, h = screen_size()
        self.move(w*0.003, h*0.27)

        self.tabs = Gtk.Notebook()
        self.tabs.connect('switch-page', self.switch_effect)
        self.add(self.tabs)

        # TODO: 
        # - make into list
        # - self.effect variable actually belongs to the layers window
        self.effect = available_effects['echo']
        
        self.sliders = []

        for e in available_effects.values():
             grid = Gtk.Grid()
             grid.set_column_spacing(15)
             grid.set_row_spacing(25)
             grid.set_column_homogeneous(True)
             grid.set_border_width(10)
             self.tabs.append_page(grid, Gtk.Label(label=e.name.capitalize()))
             sliders = []
             r = 0

             for p_idx, p in enumerate(e.pars):
                  ad = Gtk.Adjustment(value=p.startv, lower=p.minv, upper=p.maxv, 
                                      step_increment=p.incr, page_increment=p.incr, 
                                      page_size=0)

                  slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad)
                  slider.set_value_pos(Gtk.PositionType.RIGHT)
                  slider.set_digits(2) # two decimal points
                  slider.connect("value-changed", self.slider_moved, p_idx+1)
                  slider.set_vexpand(False)
                  slider.set_hexpand(True)
                  slider.set_name(p.name)

                  sliders.append(slider)


                  if p_idx % 2 == 0:
                       grid.attach(slider, 0, r, 1, 1)
                  else:
                       grid.attach(slider, 1, r, 1, 1)
                       r += 2

                  l = Gtk.Label(label=p.name.capitalize())
                  grid.attach_next_to(l, slider,
                                      Gtk.PositionType.TOP, 1, 1)
             self.sliders.append(sliders)

     def _key_press_event(self, widget, event):
          key = Gdk.keyval_name(event.keyval)
          if key in  ['1', '2', '3', '4', '5', '6', '7']:
               self.tabs.set_current_page(int(key)-1)
          elif key in ['period', 'K']:
               self.tabs.set_current_page(
                    (self.tabs.get_current_page() + 1) % self.tabs.get_n_pages())
          elif key in ['comma', 'J']:
               if self.tabs.get_current_page() == 0:
                    self.tabs.set_current_page(self.tabs.get_n_pages() - 1)
               else:
                    self.tabs.set_current_page(self.tabs.get_current_page() - 1)
          elif key == 'l':
               for s in self.sliders[self.tabs.get_current_page()]:
                    if s.props.has_focus:
                         incr = s.get_adjustment().get_step_increment()
                         s.set_value(s.get_value() + incr)
          elif key == 'h':
               for s in self.sliders[self.tabs.get_current_page()]:
                    if s.props.has_focus:
                         incr = s.get_adjustment().get_step_increment()
                         s.set_value(s.get_value() - incr)
          elif key == 'j':
               widget.do_move_focus(widget, Gtk.DirectionType.TAB_FORWARD)
          elif key == 'k':
               widget.do_move_focus(widget, Gtk.DirectionType.TAB_BACKWARD)
          elif key == 'o' and (event.state & Gdk.ModifierType.CONTROL_MASK):
               self.choose_effect_from_file()
          elif key == 's' and (event.state & Gdk.ModifierType.CONTROL_MASK):
               self.save_effect_to_file()
          elif key == 'c' and (event.state & Gdk.ModifierType.CONTROL_MASK):
               self.do_delete_event(None)
          elif key == 'Tab':
               # unbind 'Tab'
               return          

     def slider_moved(self, event, p_idx):
          # this happens automatically when switching tabs?
          self.effect.torch_rep[p_idx] = str(event.get_value())
     
     def switch_effect(self, notebook, tab, index):
          cur_page = self.tabs.get_current_page()
          if cur_page < 0:
               return
          self.effect = available_effects[notebook.get_tab_label_text(tab).lower()]

     def sliders_from_effect(self, effect_dict):
          tab_number = list(available_effects.keys()).index(effect_dict["type"])
          self.tabs.set_current_page(tab_number)

          for s in self.sliders[tab_number]:
               s.set_value(effect_dict[s.get_name()])

     def choose_effect_from_file(self):
          dialog = Gtk.FileChooserDialog(title="Choose effect...", parent=self,
                                         action=Gtk.FileChooserAction.OPEN)
          dialog.add_buttons(
               Gtk.STOCK_CANCEL,
               Gtk.ResponseType.CANCEL,
               Gtk.STOCK_OPEN,
               Gtk.ResponseType.OK,
          )

          effects_path = os.getcwd() + "/effects"
          print(effects_path, os.path.isdir(effects_path))
          if os.path.isdir(effects_path):
               dialog.set_current_folder_uri("file://" + effects_path)
          # preselect existing toml files
          from glob import glob
          preselected_file = glob("*toml")
          if preselected_file:
               dialog.set_filename(preselected_file[0])

          filter_toml = Gtk.FileFilter()
          filter_toml.set_name("TOML files")
          # no dedicated minmetype, unfortuntely
          filter_toml.add_pattern("*.toml")
          dialog.add_filter(filter_toml)

          response = dialog.run()
          if response == Gtk.ResponseType.OK:
               file_path = dialog.get_filename()
               effect_dict = toml.load(file_path)
               self.sliders_from_effect(effect_dict['effects'][0])

          dialog.destroy()

     def save_effect_to_file(self):
          save_dialog = Gtk.FileChooserDialog("Save effect to file...", self,
                                            Gtk.FileChooserAction.SAVE,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                            Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
          save_dialog.set_do_overwrite_confirmation(True)
          save_dialog.set_current_name(self.effect.name + ".toml")
          response = save_dialog.run()
          if response == Gtk.ResponseType.ACCEPT:
               # save to a toml file
               effect_dict = self.effect.to_dict()
               toml.dump({'effects' : [effect_dict]}, 
                         open(save_dialog.get_file().get_path(), 'w'))
          # close
          save_dialog.destroy()
          

     # on window delete
     def do_delete_event(self, event):
          # way faster
          os.kill(os.getpid(), signal.SIGINT)
          # self.props.application.quit()

class GlitchApplication(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self, application_id="GLITCH.GLITCH.GLITCH", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        # store CLI input in variable
        self.args = None

    def do_activate(self):
        slider_win = SliderWindow(self)
             
        # TensorGlitch takes a long time to import, which slows down -h
        import TensorGlitch
        glitcher = TensorGlitch.TensorGlitch(self.args.input)
        
        # see https://pygobject.readthedocs.io/en/latest/guide/threading.html
        if self.args.output:
             thread = threading.Thread(target=self.glitch_webcam, args=(
                  slider_win, glitcher, self.args.output))
        else:
             # only show picture window when _not_ outputing to virtual webcam
             picture_win = PictureWindow(self)
             picture_win.show_all()
             thread = threading.Thread(target=self.glitch, args=(
                  slider_win, picture_win, glitcher))

        # raise slider window
        slider_win.show_all()
        slider_win.present()
        slider_win.sliders[0][0].grab_focus()

        # read in an initial effect
        if self.args.effect:
             # an effect_dict is not a proper effect, but a shorthand representation thereof
             effect_dict = toml.load(self.args.effect)
             slider_win.sliders_from_effect(effect_dict['effects'][0])

        thread.daemon = True
        thread.start()

    # override super class
    def do_command_line(self, args):
        Gtk.Application.do_command_line(self, args) # super call

        parser = argparse.ArgumentParser(description='Live webcam glitching.')
        parser.add_argument('-i', '--input', 
                            metavar='%s/dev/video*%s' % (ef.underl,  rs.underl), 
                            default='/dev/video0', 
                            help='use /dev/video* as source (default source: /dev/video0)')
        parser.add_argument('-o', '--output', 
                            metavar='%s/dev/video*%s' % (ef.underl,  rs.underl), 
                            default=None,
                            help='output to /dev/video* (default output: Gtk Window)')
        parser.add_argument('-e', '--effect', metavar='file.toml', default=None,
                            help='launch with a particulair effect')

        self.args = parser.parse_args(args.get_arguments()[1:])
        self.do_activate()
        return 0

    # I guess Pixbuf.new(..., 8,) means an 8 bit image, with 8bits/255dec per pixel
    # 3840 = width * 3 channels
    # consider converting torch to bytes directly: https://stackoverflow.com/questions/63880081/how-to-convert-a-torch-tensor-into-a-byte-string
    # flip the GDKpixbuf somewhere? (perhaps in the drawing code)
    # - Be sure to test how much this slows down stuff
    # also consider not recreating the pixbuf, but just reusing one
    # also the new, simpler approach might be slower??
    def glitch(self, slider_win, picture_win, glitcher):
         c = GdkPixbuf.Colorspace.RGB
         while True:
              img = glitcher.glitch(slider_win.effect.torch_rep)
              b = GLib.Bytes.new(img.tobytes())
              pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(b, c, False, 8, 1280, 720, 3840)
              GLib.idle_add(picture_win.update_image, pixbuf)

    def glitch_webcam(self, slider_win, glitcher, webcam): 
         import virtualvideo
         from VirtualVideoSource import VirtualVideoSource

         fvd = virtualvideo.FakeVideoDevice()
         vidsrc = VirtualVideoSource(slider_win, glitcher)

         fvd.init_input(vidsrc)
         fvd.init_output(int(webcam[-1]), const.WIDTH, const.HEIGHT, fps=24)

         fvd.run()

    def do_startup(self):
        Gtk.Application.do_startup(self)

def main():
     warnings.filterwarnings("ignore")
     app = GlitchApplication()

     # try:
     exit_status = app.run(sys.argv)
     sys.exit(exit_status)
     # except KeyboardInterrupt:
     #      print("leaving")
     #      sys.exit(0)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
