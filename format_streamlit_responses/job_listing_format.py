import streamlit as st
import pandas as pd


def display_jobs_interactive(jobs_list: list[dict]):
    """
    Display jobs using st.data_editor with link columns
    """
    if not jobs_list:
        st.warning("No jobs to display")
        return

    df = pd.DataFrame(jobs_list)

    display_data = {
        "Job Position": df["job_position"].tolist(),
        "Company Name": df["company_name"].tolist(),
        "Apply Link": df["url"].tolist(),
    }
    display_df = pd.DataFrame(display_data)

    st.markdown("### Job Opportunities")

    # Use data_editor with link column
    st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        disabled=["Job Position", "Company Name"],
        column_config={
            "Job Position": st.column_config.TextColumn(
                "Job Position", width="large", disabled=True
            ),
            "Company Name": st.column_config.TextColumn(
                "Company Name", width="medium", disabled=True
            ),
            "Apply Link": st.column_config.LinkColumn(
                "Apply", width="small", display_text="View Job"
            ),
        },
    )
