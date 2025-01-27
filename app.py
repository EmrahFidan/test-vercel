import streamlit as st

# Title of the app
st.title('My First Streamlit App')

# Input text box
user_input = st.text_input("Enter some text")

# Display the input text
st.write("You entered:", user_input)

# Add a slider
slider_value = st.slider("Select a value", 0, 100, 50)

# Display the slider value
st.write("Slider value is:", slider_value)