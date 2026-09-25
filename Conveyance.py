 import io
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ---------------------------------------------------------
# Page Setup & Custom Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Conveyance Bill Generator", page_icon="🧾", layout="centered"
)

# Custom Colorful & Modern CSS
st.markdown(
    """
    <style>
    /* Main Background */
    .main {
        background-color: #f8fafc;
    }
    
    /* Header Gradient Banner */
    .header-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #0284c7 100%);
        padding: 28px 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
    }
    .header-container h1 {
        color: #ffffff !important;
        margin-bottom: 6px !important;
        font-weight: 800;
        font-size: 28px;
        letter-spacing: 0.5px;
    }
    .header-container h3 {
        color: #f0f9ff !important;
        margin-top: 0px !important;
        margin-bottom: 12px !important;
        font-weight: 600;
        font-size: 18px;
    }
    .header-container p {
        color: #e0f2fe !important;
        font-size: 13.5px;
        line-height: 1.5;
        max-width: 650px;
        margin: 0 auto;
        opacity: 0.95;
    }

    /* Card Box for Line Items */
    .day-card-header {
        background: #eff6ff;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 8px 14px;
        margin-bottom: 14px;
        color: #1e40af;
        font-weight: 700;
        font-size: 15px;
    }

    /* Buttons Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render Custom Header Banner with User Manual
st.markdown(
    """
    <div class="header-container">
        <h1>SHAFIQ BASAK & CO.</h1>
        <h3>Conveyance bill Create</h3>
        <p>You can create your conveyance bill without Excel! Simply enter your date, place, purpose, and rate—the site will automatically calculate amounts and generate an official PDF that you can download, print, or share.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Location to Rate Mapping (From your Excel file)
# ---------------------------------------------------------
LOCATION_RATES = {
    "Motijheel": 60,
    "Dilkusha": 80,
    "Dainik Bangla": 60,
    "Bijoynagar": 80,
    "Kakrail": 80,
    "Shantinagar": 80,
    "NBR & Segunbagicha": 80,
    "Paltan": 80,
    "Baitul Mokarram": 80,
    "Gulistan": 80,
    "Nur Mosjid": 80,
    "Shilpokola": 100,
    "Bardem Hospital": 100,
    "Kamalapur": 80,
    "Malibag": 80,
    "Mouchak": 100,
    "Mogbajar": 100,
    "Rampura": 140,
    "Bangla Motor": 100,
    "Kawran Bazar": 120,
    "Firmgate": 140,
    "Tejgaon": 140,
    "Dhanmondi": 150,
    "Mohakhali": 140,
    "Banani": 140,
    "Gulshan 1": 140,
    "Gulshan 2": 150,
    "Middle Badda": 120,
    "Uttar Badda": 140,
    "Niketon": 140,
    "Bashundhara": 180,
    "Mirpur": 180,
    "Uttara": 180,
    "Narayanganj": 200,
    "Gazipur": 300,
    "Savar": 350,
    "Chandra": 350,
    "Nayabazar": 120,
    "Dholkhal": 140,
    "Moulibazar": 180,
    "Keraniganj": 200,
    "Lalmatia": 140,
    "Shahbag": 120,
    "Kataban": 120,
    "Newmarket": 130,
    "Nilkhet": 130,
    "Sir's House": 120,
    "Jatrabari": 120,
}

PLACE_OPTIONS = list(LOCATION_RATES.keys()) + [
    "Other (Type custom location...)"
]

# ---------------------------------------------------------
# Safe Session State Initialization
# ---------------------------------------------------------
if "bill_rows" not in st.session_state or not isinstance(
    st.session_state["bill_rows"], list
):
    st.session_state["bill_rows"] = [
        {
            "DATE": "dd/mm/yy",
            "NAME OF PLACE": "Write down the place",
            "PURPOSE": "Bank/Audit/Inventory....",
            "DAYS": 1,
            "RATE": 60,
            "REMARK": "",
        },
       
    ]

if "finalized" not in st.session_state:
    st.session_state["finalized"] = False

# General Header Details
col_hdr1, col_hdr2 = st.columns(2)
with col_hdr1:
    employee_name = st.text_input(
        "👤 Prepared By (Name)",
        value="Your Name...",
        disabled=st.session_state["finalized"],
    )
with col_hdr2:
    bill_month = st.text_input(
        "📅 For the Month Ended Of",
        value="August 2026",
        disabled=st.session_state["finalized"],
    )

st.markdown("---")

# ---------------------------------------------------------
# Step 1: Form Inputs (Add, Edit, Delete)
# ---------------------------------------------------------
if not st.session_state["finalized"]:
    st.markdown("### 📝 **Edit Line Items**")

    if st.button("➕ Add New Row", type="primary"):
        new_row = {
            "DATE": "",
            "NAME OF PLACE": "Motijheel",
            "PURPOSE": "",
            "DAYS": 1,
            "RATE": 60,
            "REMARK": "",
        }
        st.session_state["bill_rows"].append(new_row)
        st.rerun()

    def update_rate_for_place(row_index):
        selected_place_key = f"place_select_{row_index}"
        rate_key = f"rate_{row_index}"
        chosen_place = st.session_state.get(selected_place_key)

        if chosen_place in LOCATION_RATES:
            st.session_state[rate_key] = LOCATION_RATES[chosen_place]

    updated_items = []
    indices_to_delete = []

    for idx, item in enumerate(st.session_state["bill_rows"]):
        st.markdown(
            f"""
            <div class="day-card-header">
                📌 Day-{idx + 1}
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([2, 3, 3])
        c4, c5, c6, c7 = st.columns([1, 1, 2, 1])

        # Date
        with c1:
            date = st.text_input(
                "Date", value=item["DATE"], key=f"date_{idx}", placeholder="DD.MM.YYYY"
            )

        # Place Selection Dropdown + Custom Input Option
        with c2:
            current_place = item["NAME OF PLACE"]

            if current_place in LOCATION_RATES:
                default_index = PLACE_OPTIONS.index(current_place)
            else:
                default_index = PLACE_OPTIONS.index(
                    "Other (Type custom location...)"
                )

            selected_option = st.selectbox(
                "Select Place",
                options=PLACE_OPTIONS,
                index=default_index,
                key=f"place_select_{idx}",
                on_change=update_rate_for_place,
                args=(idx,),
            )

            if selected_option == "Other (Type custom location...)":
                place_name = st.text_input(
                    "Type Custom Location",
                    value=current_place
                    if current_place not in LOCATION_RATES
                    else "",
                    key=f"custom_place_text_{idx}",
                    placeholder="e.g. Dhanmondi 32",
                )
            else:
                place_name = selected_option

        # Purpose
        with c3:
            purpose = st.text_input("Purpose", value=item["PURPOSE"], key=f"purpose_{idx}")

        # Days
        with c4:
            days = st.number_input(
                "Days", min_value=1, value=int(item["DAYS"]), key=f"days_{idx}"
            )

        # Rate Input
        with c5:
            if f"rate_{idx}" not in st.session_state:
                st.session_state[f"rate_{idx}"] = int(item["RATE"])

            rate = st.number_input(
                "Rate (BDT)",
                min_value=0,
                key=f"rate_{idx}",
            )

        amount = days * rate

        # Remark
        with c6:
            remark = st.text_input("Remark", value=item["REMARK"], key=f"remark_{idx}")

        # Delete Button
        with c7:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete", key=f"del_{idx}"):
                indices_to_delete.append(idx)

        updated_items.append(
            {
                "DATE": date,
                "NAME OF PLACE": place_name,
                "PURPOSE": purpose,
                "DAYS": days,
                "RATE": rate,
                "AMOUNT": amount,
                "REMARK": remark,
            }
        )

    if indices_to_delete:
        for index in sorted(indices_to_delete, reverse=True):
            updated_items.pop(index)
            st.session_state.pop(f"rate_{index}", None)
            st.session_state.pop(f"place_select_{index}", None)

        st.session_state["bill_rows"] = updated_items
        st.rerun()
    else:
        st.session_state["bill_rows"] = updated_items

st.markdown("---")

# ---------------------------------------------------------
# Step 2: Live Overview Table
# ---------------------------------------------------------
st.markdown("### 👁️ **Overview & Preview**")

df = pd.DataFrame(st.session_state["bill_rows"])

if not df.empty:
    total_amount = df["AMOUNT"].sum()

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="📊 Total Days Entered", value=len(df))
    with m2:
        st.metric(label="💰 Total Bill Amount", value=f"{total_amount} BDT")

    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("No line items added yet.")
    total_amount = 0

st.markdown("---")

# ---------------------------------------------------------
# Step 3: PDF Engine
# ---------------------------------------------------------
def create_pdf_bytes(company_name, month_str, prepared_by, items_data, total):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=1,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Heading2"],
        fontSize=13,
        alignment=1,
        spaceAfter=4,
        fontName="Helvetica",
    )

    month_style = ParagraphStyle(
        "MonthStyle",
        parent=styles["Normal"],
        fontSize=11,
        alignment=1,
        spaceAfter=15,
        fontName="Helvetica",
    )

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=0,
        fontName="Helvetica",
    )

    cell_style_bold = ParagraphStyle(
        "CellStyleBold",
        parent=styles["Normal"],
        fontSize=10,
        alignment=0,
        fontName="Helvetica-Bold",
    )

    # Document Header
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph("Conveyance Bill", subtitle_style))
    elements.append(
        Paragraph(f"For the month ended of {month_str}", month_style)
    )

    # Table Grid
    table_data = [
        ["DATE", "NAME OF PLACE", "PURPOSE", "DAYS", "RATE", "AMOUNT", "REMARK"]
    ]

    for item in items_data:
        table_data.append(
            [
                Paragraph(str(item["DATE"]), cell_style),
                Paragraph(str(item["NAME OF PLACE"]), cell_style),
                Paragraph(str(item["PURPOSE"]), cell_style),
                str(item["DAYS"]),
                str(item["RATE"]),
                str(item["AMOUNT"]),
                Paragraph(str(item["REMARK"]), cell_style),
            ]
        )

    # Total Row
    table_data.append(
        [
            Paragraph("Total", cell_style_bold),
            "",
            "",
            "",
            "",
            Paragraph(str(total), cell_style_bold),
            "",
        ]
    )

    col_widths = [70, 90, 150, 45, 45, 60, 70]
    table = Table(table_data, colWidths=col_widths)

    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("SPAN", (0, -1), (4, -1)),
    ]
    table.setStyle(TableStyle(ts))
    elements.append(table)

    elements.append(Spacer(1, 30))

    # Signature Footer
    prep_style = ParagraphStyle(
        "PrepStyle", parent=styles["Normal"], fontSize=11, fontName="Helvetica"
    )
    elements.append(
        Paragraph(f"Prepared by <b>{prepared_by}</b>", prep_style)
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------
# Step 4: Lock & Download Trigger
# ---------------------------------------------------------
col_act1, col_act2 = st.columns([1, 1])

with col_act1:
    if not st.session_state["finalized"]:
        if st.button("✅ Lock & Finalize Bill", type="primary"):
            st.session_state["finalized"] = True
            st.rerun()
    else:
        if st.button("✏️ Unlock & Edit Bill"):
            st.session_state["finalized"] = False
            st.rerun()

with col_act2:
    if st.session_state["finalized"]:
        pdf_bytes = create_pdf_bytes(
            "SHAFIQ BASAK & CO.",
            bill_month,
            employee_name,
            st.session_state["bill_rows"],
            total_amount,
        )
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=f"Conveyance_Bill_{employee_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
        )
