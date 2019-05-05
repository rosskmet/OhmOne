#Basic Ohm Script
#TODO:  Get LEDs Working / Set Up Switchable Devices (macros) / Set Up Individual Tracks (including master) / Set Up Loop Controls / Finish Designing Layout
from __future__ import with_statement
import Live
import time
from _Framework.ControlSurface import ControlSurface
from _Framework.SessionComponent import SessionComponent
from _Framework.Layer import Layer
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from _Framework.ButtonElement import ButtonElement, ButtonValue, ButtonElementMixin
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.InputControlElement import MIDI_CC_TYPE, MIDI_NOTE_TYPE, MIDI_MSG_TYPES, MIDI_NOTE_ON_STATUS, MIDI_NOTE_OFF_STATUS
from _Framework.TransportComponent import TransportComponent
from _Framework.MixerComponent import MixerComponent
from _Framework.SliderElement import SliderElement
from _Framework.DeviceComponent import DeviceComponent
from _Framework.ChannelStripComponent import ChannelStripComponent
#from _Framework.ClipSlotComponent import ClipSlotComponent
#from _Framework.SceneComponent import SceneComponent

from DeviceNavComponent import DeviceNavComponent
from ConfigurableButtonElement import ConfigurableButtonElement

"GLOBAL VARIABLES"
CHANNEL = 0  #0 to 15
is_momentary = True
LED_ON = 127
LED_OFF = 0

"MAIN MODE MIDI MAPPING (USING FACTORY OHM64 ASSIGNMENTS)"
# NOTE TYPE
SESSION_NAV_BUTTONS = [69, 77] 
SESSION_STOP_BUTTONS = [4, 12, 20, 28, 36, 44, 52] 
SCENE_LAUNCH_BUTTONS = [56, 57, 58, 59]
CLIP_LAUNCH_BUTTONS = [[0, 8, 16, 24, 32, 40, 48],
                        [1, 9, 17, 25, 33, 41, 49],
                        [2, 10, 18, 26, 34, 42, 50],
                        [3, 11, 19, 27, 35, 43, 51]]

TRACK_SELECT_BUTTONS = [65, 73, 66, 74, 67, 75, 68, 76]
TRACK_MUTE_BUTTONS = [5, 13, 21, 29, 37, 45, 53]
SEND_SELECT_BUTTONS = [6, 14, 22, 30, 38, 46]
DEVICE_NAV_BUTTONS = [7, 15]
DEVICE_BANK_BUTTONS = [54, 62]
DEVICE_LOCK_BUTTON = 60 
TRANSPORT_BUTTONS = [70, 71, 78, 79] 
LIVID_BUTTON = 87 
TWO_BUTTONS = [64, 72] 

# CC TYPE
FADERS = [23, 22, 15, 14, 5, 7, 6] 
MASTER_FADER = 4 
CROSSFADER = 24 
KNOBS_BANK_ONE = [17, 16, 9, 8, 19, 18, 11, 10] 
SEND_KNOBS = [21, 20, 13, 12, 3, 1, 0] 


class OhmOne(ControlSurface):
  __module__ = __name__
  __doc__ = "Script that creates Session Box"
  
  def __init__(self, c_instance):
    ControlSurface.__init__(self, c_instance)
    self._device_selection_follows_track_selection = True
    with self.component_guard():
      self._supress_session_highlight = True
      self._supress_send_midi = True
      self._control_is_with_automap = False
      self._setup_session_control()
      self._setup_mixer_control()
      self._setup_transport_control()
      self._setup_device_control()


  def _setup_session_control(self):
    num_tracks = 7 
    num_scenes = 4 
    session_nav_button = [ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, SESSION_NAV_BUTTONS[index]) for index in range(2)]
    session_stop_button = []

    matrix = ButtonMatrixElement()
    matrix.name = 'Button_Matrix'
    
    global session
    session = SessionComponent(num_tracks, num_scenes)
    session.name = 'Session_Control'
    session.set_offsets(0,0)
    session.set_scene_bank_buttons(session_nav_button[1], session_nav_button[0])
    #session.set_track_bank_buttons(session_nav_button[3], session_nav_button[2])

    for row in xrange(num_scenes):
      scene_launch_button = ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, SCENE_LAUNCH_BUTTONS[row])
      session_row = []
      scene = session.scene(row)
      scene.name = 'Scene' + str(row)
      scene.set_launch_button(scene_launch_button)
      scene.set_triggered_value(2)
      #scene_launch_button._set_skin_light(68)

      for column in xrange(num_tracks):
        clip_launch_button = ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, CLIP_LAUNCH_BUTTONS[row][column])
        clip_launch_button.name = str(column) + '_Clip_' + str(row) + '_Button'
        session_row.append(clip_launch_button)
        clip_slot = scene.clip_slot(column)
        clip_slot.name = str(column) + '_ClipSlot_' + str(row)
        clip_slot.set_launch_button(clip_launch_button)
        #clip_launch_button._set_skin_light(76)

      matrix.add_row(tuple(session_row))

    for column in xrange(num_tracks):
      session_stop_button.append(ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, SESSION_STOP_BUTTONS[column]))

    self._supress_session_highlight = False
    self._supress_send_midi = False
    self.set_highlighting_session_component(session)
    session.set_stop_track_clip_buttons(tuple(session_stop_button))


  def _setup_mixer_control(self):
    num_tracks = 7
    global mixer
    mixer = MixerComponent(num_tracks)
    mixer.set_track_offset(0)
    self.song().view.selected_track = mixer.channel_strip(0)._track

    master_volume_fader = SliderElement(MIDI_CC_TYPE, CHANNEL, MASTER_FADER)
    mixer.master_strip().set_volume_control(master_volume_fader)

    for index in range(num_tracks):
      mixer.channel_strip(index).set_volume_control(SliderElement(MIDI_CC_TYPE, CHANNEL, FADERS[index]))
      mixer.channel_strip(index).set_mute_button(ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, TRACK_MUTE_BUTTONS[index]))
      mixer.channel_strip(index).set_select_button(ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, TRACK_SELECT_BUTTONS[index]))
      #mixer.channel_strip(index).set_send_controls(SliderElement(MIDI_CC_TYPE, CHANNEL, SEND_KNOBS[index]))

      '''for index in range(6):
        send_select_button = ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, SEND_SELECT_BUTTONS[index])
        send_knob = SliderElement(MIDI_CC_TYPE, CHANNEL, SEND_KNOBS[index])
        current_send = []
        current_send.append(send_select_button)
        mixer.set_send_controls(send_knob)
        
      mixer._send_index.append(current_send)'''

    #for index in range(num_tracks):
      #track_select_button = [ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, TRACK_SELECT_BUTTONS[index]) for index in range (7)]
      #selected_track = track_select_button[index]
      #self.song().view.selected_track = mixer.channel_strip(selected_track)._track
  

  def _setup_transport_control(self):
    transport_button = [ConfigurableButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, TRANSPORT_BUTTONS[index]) for index in range(4)]
    #transport_button.set_on_off_values(LED_ON, LED_OFF)
    transport = TransportComponent()
    transport.set_play_button(transport_button[0])
    transport.set_stop_button(transport_button[1])


  def _setup_device_control(self):
    self._device = DeviceComponent(None, True)
    self._channel_strip = ChannelStripComponent()
    self._device.name = 'Device_Component'
    lock_button = ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, DEVICE_LOCK_BUTTON)
    self._device.set_lock_button(lock_button)

    device_parameters = []
    for index in range(8):
      macro_knobs = SliderElement(MIDI_CC_TYPE, CHANNEL, KNOBS_BANK_ONE[index])
      device_parameters.append(macro_knobs)
    
    self._device.set_parameter_controls(device_parameters)
    self.set_device_component(self._device) #Why not self._device.set_device_component()

    #device_nav_button = [ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, DEVICE_NAV_BUTTONS[index]) for index in range(2)]
    #self._device.s

    #bank_button = [ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, DEVICE_BANK_BUTTONS[index]) for index in range(2)]
    #self._device.set_bank_prev_button(bank_button[0])
    #self._device.set_bank_next_button(bank_button[1])


  def disconnect(self):
    self.log_message(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + "----------Session_Box----------")    
    ControlSurface.disconnect(self)
    return None
