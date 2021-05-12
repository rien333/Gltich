# TODO
# To check out (most require special care/code):
# - compand, dither, fade, stretch, tempo, vol
# Allow for more parameter types than discrete/nondiscrete, and add seperate callbacks for each

from collections import OrderedDict
import toml

class Effect():
    def __init__(self, name, start_vals=[]):
        extra_par = None
        self.name = name
        if self.name == 'echo': 
            self.pars = [Par('gain-in', False, 0, 1, 0.1, 0.6), 
                         Par('gain-out', False, 0, 1, 0.1, 0.6),
                         Par('delay', False, 0.1, 2000, 0.1, 10), 
                         Par('decay', False, 0, 1, 0.1, 0.79)]
        elif self.name == 'reverb':
            self.pars = [Par('reverberance', False, 0, 100, 0.5, 3), 
                         Par('dampening', False, 0, 100, 0.5, 5), 
                         Par('room-scale', False, 0, 100, 0.05, 1),
                         Par('stereo-depth', False, 0, 100, 0.05, 0.05),
                         Par('pre-delay', False, 0, 100, 0.05, 1),
                         Par('wet-gain', False, -10, 10, 0.05, 3)]
        elif self.name == 'lowpass':
            self.pars = [Par('high', False, 0.01, 10, 0.05, 3), 
                         Par('low', False, 0.01, 10, 0.05, 5)]
        elif self.name == 'overdrive':
            self.pars = [Par('gain', False, 0, 100, 0.2, 3), 
                         Par('colour', False, 0, 100, 0.2, 5)]
        elif self.name == 'chorus':
            self.pars = [Par('gain-in', False, 0, 1, 0.1, 0.7), 
                         Par('gain-out', False, 0, 1, 0.1, 0.7),
                         Par('delay', False, 20, 100, 0.8, 55), 
                         Par('decay', False, 0, 1, 0.1, 0.4), 
                         Par('speed', False, 0.1, 5, 0.01, 0.25),
                         Par('depth', False, 0, 10, 0.1, 2),
                         ]
            extra_par = '-t'
        elif self.name == 'treble':
            self.pars = [Par('gain', False, -120, 120, 10, 3), 
                         Par('frequency', False, 0.01, 3000, 10, 5),
                         Par('width', False, 0.01, 1, 0.05, 0.2)]
        elif self.name == 'bass':
            self.pars = [Par('gain', False, -120, 120, 10, 3), 
                         Par('frequency', False, 0.01, 3000, 10, 5),
                         Par('width', False, 0.01, 1, 0.05, 0.2)]
        elif self.name == 'biquad':
            self.pars = [Par('b0', False, 0.01, 1, 0.01, 0.85),
                         Par('b1', False, 0.01, 1, 0.01, 0.75),
                         Par('b2', False, 0.01, 1, 0.01, 1.0),
                         Par('a0', False, 0.01, 1, 0.01, 0.2),
                         Par('a1', False, 0.01, 1, 0.01, 0.17),
                         Par('a2', False, 0.01, 1, 0.01, 0.2)]
        elif self.name == 'allpass':
            self.pars = [Par('frequency', False, 0.01, 3000, 10, 5),
                         Par('width', False, 0.01, 1, 0.05, 0.2)]
        elif self.name == 'pitch':
            self.pars = [Par('shift', False, 0, 20, 0.01, 0.0),
                         Par('segment', False, 12, 110, 1, 100),
                         Par('search', False, 0, 30, 0.1, 0.2),
                         Par('overlap', False, 0, 30, 0.1, 0.0),
                        ]
        elif self.name == 'equalizer':
            self.pars = [Par('frequency', False, 0.01, 4000, 10, 277.56),
                         Par('width', False, 0.01, 2, 0.05, 0.01), 
                         Par('gain', False, -200, 200, 0.55, 110),]
        elif self.name == 'flanger':
            # misses some pars unfortuntely
            self.pars = [Par('delay', False, 0, 30, 0.1, 1),
                         Par('depth', False, 0, 10, 0.1, 1), 
                         Par('regen', False, -95, 95, 0.1, 10),
                         Par('width', False, 0, 100, 0.1, 1), 
                         Par('speed', False, 0.1, 10, 0.05, 1), 
                         ]
        elif self.name == 'speed':
            self.pars = [Par('factor', False, 1, 1000, 0.1, 1), ]
        elif self.name == 'vol':
            self.pars = [Par('speed', False, 0.1, 120, 1, 3), 
                         Par('depth', False, 0.1, 100, 10, 5),]
        else:
            print("effect", name, "not found.")
            exit(0)

        self.torch_rep = [self.name]
        if start_vals:
            self.torch_rep += [str(v) for v in start_vals]
        else:
            self.torch_rep += [str(p.startv) for p in self.pars]
        if extra_par:
            self.torch_rep.append(extra_par)

    def to_dict(self):
        """
        Dictionary representation of an effect.
        Suitable for saving to a toml file.
        """
        
        effect_dict = {"type" : self.name}
        for p, n in zip(self.pars, self.torch_rep[1:]):
            effect_dict[p.name] = float(n)
        return effect_dict


    def __str__(self):
        return str(self.torch_rep)

class Par():
    def __init__(self, name, discrete, minv=0, maxv=1, incr=0.1, startv=0.5):
        self.name = name
        self.minv = minv
        self.maxv = maxv
        self.incr = incr
        self.startv = startv

available_effects = OrderedDict({'echo' : Effect('echo'), 'reverb' : Effect('reverb'), 'chorus' : Effect('chorus'),  'treble' : Effect('treble'), 'biquad' : Effect('biquad'), 'pitch' : Effect('pitch'), 'equalizer' : Effect('equalizer')})
