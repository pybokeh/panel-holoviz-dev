import panel as pn
import numpy as np

def generate_random_number(event=None):
    static_text.value = np.random.randint(low=100000, high=200000)

static_text = pn.widgets.StaticText(name='Random Number Generator', value='')

generate_button = pn.widgets.Button(name='Generate New Number')
generate_button.on_click(generate_random_number)

app = pn.Column(generate_button, static_text)
app.servable()
