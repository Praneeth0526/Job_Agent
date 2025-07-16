# main_form_filler.py
import pyautogui
import time

# --- Configuration ---
# Enable PyAutoGUI's failsafe feature: moving the mouse to a corner of the
# screen will raise an exception and stop the script.
pyautogui.FAILSAFE = True


# --- Main Functions ---

def get_and_display_screen_size():
    """
    Gets and prints the primary monitor's screen resolution.
    """
    print("Getting screen size...")
    screenWidth, screenHeight = pyautogui.size()
    print(f"Screen Resolution: {screenWidth} x {screenHeight}")
    return screenWidth, screenHeight


def get_mouse_position_helper():
    """
    A helper function to display the mouse's current X, Y coordinates.
    Run this part of the script by itself to find the coordinates you need
    for your specific form fields.
    """
    print("Move your mouse over a target element and wait...")
    print("Press Ctrl-C to quit.")
    try:
        while True:
            x, y = pyautogui.position()
            positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
            print(positionStr, end='')
            print('\b' * len(positionStr), end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nDone.')


def automate_form_filling():
    """
    Automates filling a hypothetical form after a delay.

    IMPORTANT: You MUST replace the example coordinates below with the actual
    coordinates of the form fields on your screen. Use the
    get_mouse_position_helper() function to find them.
    """
    # --- Example Data to be Typed ---
    first_name = "John"
    last_name = "Doe"
    email = "johndoe.example@email.com"
    comments = "I am very interested in this position and believe my skills in Python and automation would be a great asset to your team."

    # --- Automation Sequence ---
    print("\nStarting form automation in 5 seconds...")
    print("Please switch to the window with the form you want to fill.")
    print("To stop the script at any time, move your mouse to a screen corner.")
    time.sleep(5)

    try:
        # Example coordinates - REPLACE THESE
        # These would be the (x, y) positions of your form fields.
        first_name_field_coords = (500, 350)
        last_name_field_coords = (500, 400)
        email_field_coords = (500, 450)
        comments_field_coords = (500, 550)
        submit_button_coords = (500, 650)

        print("Filling out the form...")

        # 1. Click on the 'First Name' field and type.
        pyautogui.click(first_name_field_coords)
        pyautogui.write(first_name, interval=0.05)

        # 2. Click on the 'Last Name' field and type.
        pyautogui.click(last_name_field_coords)
        pyautogui.write(last_name, interval=0.05)

        # 3. Click on the 'Email' field and type.
        pyautogui.click(email_field_coords)
        pyautogui.write(email, interval=0.05)

        # 4. Click on the 'Comments' text area and type.
        pyautogui.click(comments_field_coords)
        pyautogui.write(comments, interval=0.02)

        # 5. Click the submit button.
        # UNCOMMENT THE LINE BELOW TO ACTUALLY CLICK SUBMIT
        # pyautogui.click(submit_button_coords)

        print("\nForm automation complete.")
        print("The 'Submit' button was not clicked as a safety measure.")

    except pyautogui.FailSafeException:
        print("\nFailsafe triggered. Script stopped.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")


# --- Execution ---

if __name__ == "__main__":
    print("--- PyAutoGUI Form Filler ---")

    # You can run this function by itself to find coordinates.
    # To do so, comment out automate_form_filling() and uncomment below:
    # get_mouse_position_helper()

    # Run the main automation function
    automate_form_filling()

    print("\n--- Script Finished ---")
