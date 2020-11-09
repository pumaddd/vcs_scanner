from app.modules.source import BaseSource
from gnuradio import gr
from gnuradio import blocks
from gnuradio import uhd
from gnuradio.filter import firdes
from grgsm import arfcn
from math import pi
import grgsm

class source(BaseSource):
    
    __info__ = {
    'name': 'USRP Source',
    'device': 'USRP',
    'description': 'driver module to run USRP hardware device'
    }

    def __init__(self, **kw):
        super(source, self).__init__(**kw)
        
    def source_init(self):
        gr.hier_block2.__init__(
            self, "SDRPLAY Source",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
        )

        ##################################################
        # Blocks
        ##################################################
        self.sdr_source = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )

        self.set_fc(self.fc)
        self.set_samp_rate(self.samp_rate)
        self.set_gain(self.gain)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.sdr_source, 0),  (self, 0)) 
        print("[USRP SOURCE] initulize source with fc {}, sample rate {}, gain {}".format(self.fc, self.samp_rate, self.gain))

    def get_fc(self):
        return self.fc

    def set_fc(self, fc, offset=0):

        self.fc = fc
        self.sdr_source.set_center_freq(self.fc, 0)
        print("[USRP SOURCE]set to frequency {} in file {} sample rate {}")

    def get_osr(self):
        return self.osr

    def set_osr(self, osr):
        self.osr = osr
        self.set_samp_rate_out(self.osr*self.gsm_symb_rate)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.sdr_source.set_samp_rate(self.samp_rate)
   
    def set_gain(self, gain):
        self.gain = gain
        self.sdr_source.set_gain(self.gain, 0)
    
    @staticmethod
    def probe():
        uhd_devices = uhd.find_devices()
        if not uhd_devices:
            return False
        
        return True
