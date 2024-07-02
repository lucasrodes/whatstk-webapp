"""Streamlit-based app to parse whatsapp chats.

Uses whatstk.
"""

from pathlib import Path
import streamlit as st
import tempfile
from whatstk import df_from_whatsapp
from whatstk import FigureBuilder
from streamlit_extras.buy_me_a_coffee import button as coffee_button


# Page settings
st.set_page_config(
    page_title="WhatsApp chat parser",
    page_icon="favicon.png",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None
)
hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)

# APP title
st.title('WhatsApp chat parser')
st.markdown("**⚡ Powered by [whatstk](https://github.com/lucasrodes/whatstk)**")


# Side bar
with st.sidebar:
    hformat = st.text_input(
        "Header format",
        help="More info at https://whatstk.readthedocs.io/en/stable/source/getting_started/hformat.html.",
    )
    encoding = st.text_input(
        "Encoding",
        value="utf-8",
        help="Encoding of the chat.",
    )

# Encoding default
ENCODING_DEFAULT = "utf-8"

# Privacy message & toast
msg_privacy = (
    "**Privacy policy**"
    "\n\n"
    "All your uploaded files are deleted once you leave the page. "
    "Your files are _only_ used to automatically generate your visualisations and a CSV file for you. "
    "Your files are never accessed by any human, and remain totally private. "
    "All the code used to run this site is [public](https://github.com/lucasrodes/whatstk-webapp/)"
)

# st.toast(
#     msg_privacy,
#     icon="🔒"
# )


# Upload file box
uploaded_file = st.file_uploader(
    label="Upload your WhatsApp chat file ([learn more](https://whatstk.readthedocs.io/en/stable/source/getting_started/export_chat.html)).",
    type=["txt", "zip"],
    # label_visibility="collapsed",
)
# Define temporary file (chat will be stored here temporarily)
temp_dir = tempfile.TemporaryDirectory()
uploaded_file_path = Path(temp_dir.name) / "chat"

if uploaded_file is not None:
    with open(uploaded_file_path, 'wb') as output_temporary_file:
        output_temporary_file.write(uploaded_file.read())

    # Load file as dataframe
    try:
        df = df_from_whatsapp(
            output_temporary_file.name,
            hformat=hformat,
            encoding=encoding,
        )
    except Exception as e:
        st.error(
            "The chat could not be parsed automatically! You can try to set custom `hformat` "
            "value in the side bar config."
            "Additionally, please report to https://github.com/lucasrodes/whatstk/issues. If possible, "
            "please provide a sample of your chat (feel free to replace the actual messages with dummy text)."
        )
        with open(output_temporary_file.name, 'rb') as f:
            print("Sample of the chat (for debugging purposes):")
            print(f.read(1000).decode())
        st.stop()
    else:
        # Remove system messages
        sys_msgs = [
            # r"Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.",
            r".?Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.",
            r".?Group creator created this group",
            r".?\screated this group",
            r".?You were added",
        ]
        for sys_msg in sys_msgs:
            mask = df['message'].str.fullmatch(sys_msg)
            df = df[~mask]

        if df["username"].nunique() > 2:
            # Get username of the system
            username_system = []
            for sys_msg in sys_msgs:
                mask = df['message'].str.fullmatch(sys_msg)
                username_system += list(df.loc[mask, "username"])
            df = df[~df["username"].isin(set(username_system))]
        # Download option
        csv = df.to_csv().encode(ENCODING_DEFAULT)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='chat.csv',
            mime='text/csv',
            help="Download the formatted chat as a CSV file",
        )

        # Visualisations
        st.header("Visualisations")
        # Print chat as dataframe
        tab1, tab2, tab3, tab4 = st.tabs(["Number of messages sent", "Length of messages", "User interaction", "Table"])
        # FigureBuilder
        fb = FigureBuilder(df=df)

        with tab1:
            # Countring mode
            count_mode = st.radio(
                "Counting mode",
                ("Number of messages sent", "Number of characters sent"),
                horizontal=True,
            )
            # Aggregate all users or disaggregated by user?
            all_users = st.radio(
                "Aggregate all users",
                ("Yes", "No"),
                horizontal=True,
                index=1,
            )
            all_users = True if all_users == "Yes" else False
            if count_mode == "Number of messages sent":
                figs = [
                    fb.user_interventions_count_linechart(
                        cumulative=True,
                        title='Number of messages sent (cumulative)',
                        msg_length=False,
                        all_users=all_users,
                    ),
                    fb.user_interventions_count_linechart(
                        date_mode='hour',
                        title='Number of messages sent (per hour in a day)',
                        xlabel='Hour',
                        msg_length=False,
                        all_users=all_users,
                    ),
                ]
            else:
                figs = [
                    fb.user_interventions_count_linechart(
                        cumulative=True,
                        title='Number of characters sent (cumulative)',
                        msg_length=True,
                        all_users=all_users,
                    ),
                    fb.user_interventions_count_linechart(
                        date_mode='hour',
                        title='Number of characters sent (per hour in a day)',
                        xlabel='Hour',
                        msg_length=True,
                        all_users=all_users,
                    ),
                ]
            for fig in figs:
                st.plotly_chart(fig)

        with tab2:
            fig = fb.user_msg_length_boxplot()
            st.plotly_chart(fig)
        with tab3:
            fig = fb.user_message_responses_heatmap()
            st.plotly_chart(fig)

        with tab4:
            st.dataframe(df)

st.divider()
st.markdown("🔒 " + msg_privacy)

coffee_button(username="lucasrg", bg_color="ffffff", coffee_color="FFDD00")
