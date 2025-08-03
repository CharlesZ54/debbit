import logging
import os
import time

from selenium.webdriver.support.wait import WebDriverWait

LOGGER = logging.getLogger('debbit')


# converts cents int to formatted dollar string
# 4 -> '0.04'
# 50 -> '0.50'
# 160 -> '1.60'
# 12345 -> '123.45'
def cents_to_str(cents):
    if cents < 10:
        return '0.0' + str(cents)
    elif cents < 100:
        return '0.' + str(cents)
    else:
        return str(cents)[:-2] + '.' + str(cents)[-2:]


# Removes all non-number characters and returns an int
# '$77.84' -> 7784
# 'balance: 1.50' -> 150
# '0.05' -> 5
def str_to_cents(string):
    return int(''.join([c for c in string if c.isdigit()]))


# This lambda function finishes the moment either element is visible.
# Returns False if element found indicating that we need to log in.
# Returns True if element found indicating that we are already logged in.
#
# To experiment with what to pass in here, try executing statements like these
# while your debugger is paused in your merchant's web_automation() function:

# driver.find_element(By.ID, 'some-element-id')
# driver.find_element(By.XPATH, "//*[contains(text(),'some text on webpage')]")
def is_logged_in(driver, timeout=30, logged_out_element=None, logged_in_element=None):
    login_status = WebDriverWait(driver, timeout).until(
        lambda driver:
        (driver.find_elements(*logged_out_element) and 'logged_out')
        or
        (driver.find_elements(*logged_in_element) and 'logged_in')
    )

    if login_status == 'logged_out':  # TODO is there any way we know this is a use_cookies:yes secondary purchase?
        LOGGER.info('login_status=logged_out, logging in now')
        return False
    else:
        LOGGER.info('login_status=logged_in')
        return True


# Useful with WebDriverWait() and multiple expected conditions.
# This function finishes the moment any condition returns true.
# Example usage:
#
# try:
#     WebDriverWait(driver, 30).until(utils.AnyExpectedCondition(
#         expected_conditions.element_to_be_clickable((By.ID, 'some-element-id')),
#         expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'some text on webpage')]")),
#         expected_conditions.element_to_be_clickable((By.XPATH, "//img[contains(@src,'someDescription')]"))
#     ))
# except TimeoutException:
#     LOGGER.info('Timed out looking for expected conditions after 30 seconds')
class AnyExpectedCondition:
    def __init__(self, *args):
        self.expected_conditions = args

    def __call__(self, driver):
        for condition in self.expected_conditions:
            try:
                if condition(driver):
                    return True
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass

        return False


def is_running_in_docker():
    """Check if the application is running inside a Docker container"""
    return os.path.exists('/.dockerenv')


def get_otp_input(prompt_text, merchant_id=None):
    """
    Get OTP input from various sources:
    1. Interactive input (if not in Docker)
    2. Docker command-line interface (if in Docker)
    """
    # If in Docker, provide command-line interface
    if is_running_in_docker():
        LOGGER.info("=" * 60)
        LOGGER.info("OTP REQUIRED - DOCKER CONTAINER")
        LOGGER.info("=" * 60)
        LOGGER.info(f"OTP needed for: {prompt_text}")
        if merchant_id:
            LOGGER.info(f"Merchant ID: {merchant_id}")
        LOGGER.info("")
        LOGGER.info("To provide the OTP, run this command in your terminal:")
        LOGGER.info("")
        LOGGER.info(f"docker exec -it $(docker ps -q --filter ancestor=debbit) python3 -c \"import debbit; debbit.provide_otp('{merchant_id or 'default'}', input('Enter OTP: '))\"")
        LOGGER.info("")
        LOGGER.info("Or use this simpler command:")
        LOGGER.info(f"docker exec -it $(docker ps -q --filter ancestor=debbit) bash -c 'echo \"Enter OTP: \" && read otp && python3 -c \"import debbit; debbit.provide_otp(\\\"{merchant_id or 'default'}\\\", \\\"$otp\\\")\"'")
        LOGGER.info("")
        LOGGER.info("Or use the helper script:")
        LOGGER.info(f"./provide_otp.sh debbit {merchant_id or 'default'}")
        LOGGER.info("")
        LOGGER.info("Waiting for OTP...")
        
        # Wait for OTP to be provided
        while True:
            try:
                # Check if OTP file exists (created by provide_otp function)
                otp_file = f"/tmp/debbit_otp_{merchant_id or 'default'}"
                if os.path.exists(otp_file):
                    with open(otp_file, 'r') as f:
                        otp = f.read().strip()
                    os.remove(otp_file)  # Clean up
                    LOGGER.info("OTP received, proceeding...")
                    return otp
                time.sleep(1)
            except KeyboardInterrupt:
                LOGGER.error("OTP input interrupted by user")
                raise Exception("OTP input interrupted")
    
    # Fall back to interactive input (only in non-Docker environments)
    LOGGER.info(prompt_text)
    return input()


def provide_otp(merchant_id, otp_code):
    """
    Function to be called from outside the container to provide OTP
    """
    otp_file = f"/tmp/debbit_otp_{merchant_id}"
    with open(otp_file, 'w') as f:
        f.write(otp_code)
    LOGGER.info(f"OTP provided for {merchant_id}")
