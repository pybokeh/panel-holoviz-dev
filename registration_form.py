import panel as pn

first_name_label = pn.pane.Markdown('**Enter your first name:**')
last_name_label = pn.pane.Markdown('**Enter your last name:**')
email_label = pn.pane.Markdown('**Enter your email:**')

# Generic function, can easily make this into a SQL INSERT statement
def display_inputs(event=None):
    first_name_text.value = first_name_input.value
    last_name_text.value = last_name_input.value
    email_text.value = email_input.value

def clear_inputs(event=None):
    first_name_input.value = ''
    last_name_input.value = ''
    email_input.value = ''
    first_name_text.value = ''
    last_name_text.value = ''
    email_text.value = ''

first_name_input: str = pn.widgets.TextInput()
last_name_input: str = pn.widgets.TextInput()
email_input: str = pn.widgets.TextInput()

register_button = pn.widgets.Button(name='Register')
register_button.on_click(display_inputs)

clear_button = pn.widgets.Button(name='Clear all fields')
clear_button.on_click(clear_inputs)

first_name_text = pn.widgets.StaticText(name='First name', value='')
last_name_text = pn.widgets.StaticText(name='Last name', value='')
email_text = pn.widgets.StaticText(name='Email', value='')

# Layout components in a column-wise or row-wise fashion
app = pn.Column(first_name_label,
                first_name_input,
                last_name_label,
                last_name_input,
                email_label,
                email_input,
                pn.Row(register_button, clear_button),
                first_name_text,
                last_name_text,
                email_text
)

app.servable()
