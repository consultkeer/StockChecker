import requests
import smtplib
import csv
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Google Sheets setup for public sheets
def fetch_google_sheet(sheet_id, gid):
    """
    Fetch data from a specific sheet within a Google Sheets file.

    :param sheet_id: The ID of the Google Sheets document.
    :param gid: The GID (unique ID) of the specific sheet/tab.
    :return: A list of rows as dictionaries.
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    if response.status_code == 200:
        decoded_content = response.content.decode('utf-8')
        reader = csv.reader(decoded_content.splitlines())
        return [row for row in reader]
    else:
        print(f"Failed to fetch data from Sheet GID {gid}. Status code: {response.status_code}")
        return []

# Check stock status and extract product names with colors
def get_out_of_stock_items(urls):
    out_of_stock_items = []

    for url in urls:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract product name
            product_name_tag = soup.find('h1', class_='productView-title')
            if product_name_tag:
                product_name = product_name_tag.get_text(strip=True)
            else:
                product_name = "Unknown Product"

            # Extract color (checked input indicates selected color)
            color_tag = soup.find('fieldset', class_='product-form__input', attrs={'data-product-attribute': 'set-rectangle'})
            color = "Unknown Color"
            if color_tag:
                checked_input = color_tag.find('input', {'checked': True})
                if checked_input:
                    color = checked_input.get('value', 'Unknown Color')

            # Combine product name and color
            product_name_with_color = f"{product_name} ({color})"

            # Check stock status
            button = soup.find('button', class_='product-form__submit')
            if button and 'Sold out' in button.get_text() and button.has_attr('disabled'):
                out_of_stock_items.append((product_name_with_color, url))  # Append name with URL
        else:
            print(f"Failed to fetch the page for {url}")

    return out_of_stock_items

# Send email with product names hyperlinked to their respective URLs
def send_email(to_email, out_of_stock_items_with_urls):
    from_email = "consultkeerthan@gmail.com"
    from_password = "nevz gfbi ocqc sduh"

    subject = "Out of Stock Notification"
    
    # Create the HTML email body with hyperlinks
    body = "The following items are out of stock:<br><br>"
    body += "<ul>"
    for product_name, url in out_of_stock_items_with_urls:
        body += f'<li><a href="{url}" target="_blank">{product_name}</a></li>'
    body += "</ul>"

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'html'))  # Set email content type to HTML

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

# Main function
def main():
    # Replace with your Google Sheet ID
    sheet_id = "1rEWuNwnxkJ8nWyz__lqJbNvykOp5jjtm1iSIADdskQI"

    # GIDs for the respective sheets
    email_gid = "0"  # Replace with the actual GID for the 'email' sheet
    url_gid = "65880526"  # Replace with the actual GID for the 'url' sheet

    # Fetch data from both sheets
    email_data = fetch_google_sheet(sheet_id, email_gid)
    url_data = fetch_google_sheet(sheet_id, url_gid)

    if not email_data or not url_data:
        print("Failed to retrieve data from Google Sheets.")
        return

    # Extract email addresses and URLs (assuming they are on the first row)
    emails = email_data[0][0].split(',')  # Emails are in the first column of the email sheet
    urls = url_data[0][0].split(',')      # URLs are in the first column of the URL sheet

    # Check stock status
    out_of_stock_items_with_urls = get_out_of_stock_items(urls)

    # Send emails to all recipients
    for email in emails:
        if out_of_stock_items_with_urls:
            send_email(email, out_of_stock_items_with_urls)
        else:
            print(f"No out-of-stock items to notify for {email}.")

if __name__ == "__main__":
    main()
