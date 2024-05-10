import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

# Now you can continue with the rest of your code
from gtts import gTTS
import os

def play_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save('response.mp3')  # Save the spoken text to an mp3 file
    # Set up a simple GStreamer pipeline to play audio
    player = Gst.ElementFactory.make("playbin", "player")
    player.set_property('uri', 'file://' + os.path.abspath('response.mp3'))
    player.set_state(Gst.State.PLAYING)
    # Wait until error or EOS
    bus = player.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
    # Free resources
    player.set_state(Gst.State.NULL)

# Example usage
if __name__ == "__main__":
    text = "Hello, this is a test text to speech output."
    play_text(text)
