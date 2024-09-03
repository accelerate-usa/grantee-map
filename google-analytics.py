#%%
import os

# Specify the folder containing your HTML files
folder_path = './esser-expenditures/figures'  # Replace with your folder path

# Specify your Google Analytics tracking ID
tracking_id = 'G-09KK2TCTB4'  # Replace with your Google Analytics tracking ID

# Iterate over all files in the specified folder
for filename in os.listdir(folder_path):
    if filename.endswith('.html'):
        # Create title, description, image URL, and page URL based on the filename
        page_title = filename.replace('.html', '')
        page_description = f"A detailed view of {page_title}."
        page_image_url = f"https://log.jasongodfrey.info/img/{page_title}.png"
        page_url = f"https://log.jasongodfrey.info/html-files/{page_title}.html"

        # Google Analytics script and Open Graph meta tags to be inserted
        ga_script = f"""
            <!-- Google tag (gtag.js) -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
            <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());

            gtag('config', '{tracking_id}');
            </script>

            <!-- Open Graph meta tags -->
            <meta property="og:title" content="{page_title}" />
            <meta property="og:description" content="{page_description}" />
            <meta property="og:image" content="{page_image_url}" />
            <meta property="og:url" content="{page_url}" />
            <meta property="og:type" content="website" />
        """

        file_path = os.path.join(folder_path, filename)

        # Read the HTML file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Insert the GA script just after the <head> tag
        modified_html_content = html_content.replace('<head>', f'<head>\n{ga_script}')

        # Save the modified HTML content back to the file with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(modified_html_content)

        print(f'Added Google Analytics tracking and Open Graph tags to {filename}')

print('All HTML files have been processed.')


# %%
