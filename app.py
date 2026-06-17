import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Attendance Tracker", layout="centered")
st.title("Attendance Tracker App 📊")
st.write("Apni Master Excel file aur Daily CSV files upload karein aur total attendance nikalein.")

st.subheader("1. Upload Master Data")
master_file = st.file_uploader("Master Excel File upload karein (xlsx/csv)", type=['xlsx', 'csv'])

st.subheader("2. Upload Daily Attendance")
daily_files = st.file_uploader("Daily CSV files upload karein", type=['csv'], accept_multiple_files=True)

if st.button("Calculate Attendance"):
    if master_file is not None and len(daily_files) > 0:
        try:
            if master_file.name.endswith('.csv'):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)
            
            if 'Total Attendance' not in master_df.columns:
                master_df['Total Attendance'] = 0
            else:
                master_df['Total Attendance'] = 0 

            all_unmatched_names = []

            for file in daily_files:
                daily_df = pd.read_csv(file)
                col_name = None
                for col in daily_df.columns:
                    if 'name' in col.lower() or 'participant' in col.lower():
                        col_name = col
                        break
                
                if col_name:
                    daily_df[col_name] = daily_df[col_name].fillna("")
                    raw_names = daily_df[col_name].astype(str).str.strip().tolist()
                    
                    matched_in_this_file = set()
                    cleaned_to_raw_map = {}
                    
                    # SUPER CLEANING: Sirf alphabets aur numbers rakhenge
                    for raw in raw_names:
                        if raw:
                            clean_name = re.sub(r'[^a-z0-9]', '', str(raw).lower())
                            cleaned_to_raw_map[clean_name] = raw
                    
                    for index, row in master_df.iterrows():
                        name = str(row.get('Student Name', '')).replace('nan', '').strip().lower()
                        p_id = str(row.get('pariticipant_id', '')).replace('nan', '').strip().lower() 
                        
                        last_3 = p_id[-3:] if len(p_id) >= 3 else p_id
                        first_name = name.split()[0] if " " in name else name
                        name_no_space = name.replace(" ", "")
                        
                        # 1. Without ID targets (Safe for exact match)
                        valid_exact_only = set([name_no_space, first_name])
                        for part in name.split():
                            valid_exact_only.add(part)

                        # 2. With ID targets (Safe for substring match like abhi046)
                        valid_with_id = set()
                        valid_with_id.add(f"{name_no_space}{last_3}")
                        valid_with_id.add(f"{first_name}{last_3}")
                        if len(first_name) >= 4: valid_with_id.add(f"{first_name[:4]}{last_3}") # First 4 chars + ID
                        if len(first_name) >= 5: valid_with_id.add(f"{first_name[:5]}{last_3}") # First 5 chars + ID

                        student_matched = False
                        
                        for clean_name in cleaned_to_raw_map.keys():
                            # Condition 1: Exact Name Match (bina ID ke aaye bacho ke liye)
                            if clean_name in valid_exact_only:
                                student_matched = True
                                matched_in_this_file.add(clean_name)
                                break
                            
                            # Condition 2: Short Name/Full Name with ID (e.g., abhi046, akash047)
                            for v_id in valid_with_id:
                                if v_id in clean_name:
                                    student_matched = True
                                    matched_in_this_file.add(clean_name)
                                    break
                                    
                            if student_matched:
                                break
                                
                        if student_matched:
                            master_df.at[index, 'Total Attendance'] += 1
                            
                    # Unmatched names collect karna
                    for clean_name, raw_name in cleaned_to_raw_map.items():
                        if clean_name not in matched_in_this_file:
                            all_unmatched_names.append(raw_name)
                            
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            
            total_students = len(master_df)
            present_today = (master_df['Total Attendance'] > 0).sum()
            
            st.metric(label="🟢 Today Total Present Students", value=f"{present_today} / {total_students}")
            
            if all_unmatched_names:
                st.warning("⚠️ Neeche diye gaye naam Master list se match nahi hue:")
                st.write(list(set(all_unmatched_names))) 

            st.dataframe(master_df) 

            csv = master_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Final Report",
                data=csv,
                file_name='Final_Attendance_Report.csv',
                mime='text/csv',
            )
            
        except Exception as e:
            st.error(f"Koi error aayi hai. Error details: {e}")
    else:
        st.warning("Pehle Master Excel file aur kam se kam ek Daily CSV file upload karein!")
