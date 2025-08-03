import logging
import random
import time

from selenium import common
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException, \
    ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

import utils
from result import Result

LOGGER = logging.getLogger('debbit')


def web_automation(driver, merchant, amount):
    driver.get('https://www.amazon.com/dp/B0CHTVMXZJ')

    WebDriverWait(driver, 90).until(expected_conditions.element_to_be_clickable((By.ID, "gcui-asv-reload-buynow-button")))
    for i in range(300):
        if driver.find_element(By.ID, "gcui-asv-reload-buynow-button").text == 'Buy Now':  # wait for 'Loading...' text to turn into 'Buy Now'
            break
        time.sleep(0.1)

    time.sleep(1 + random.random() * 2)  # slow down automation randomly to help avoid bot detection
    
    # Enter the amount first
    driver.find_element(By.ID, 'gc-ui-form-custom-amount').send_keys(utils.cents_to_str(amount))
    time.sleep(1 + random.random() * 2)  # slow down automation randomly to help avoid bot detection
    driver.find_element(By.ID, "gcui-asv-reload-buynow-button").click()

    # Wait for login page or checkout page to appear
    try:
        WebDriverWait(driver, 90).until(utils.AnyExpectedCondition(
            expected_conditions.element_to_be_clickable((By.ID, 'ap_email')),  # first time login (old)
            expected_conditions.element_to_be_clickable((By.ID, 'ap_email_login')),  # first time login (new)
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'" + merchant.usr + "')]")),  # username found on login page
            # Already logged in
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Order Summary')]")),  # Checkout page
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'a payment method')]"))  # Another version of the checkout page
        ))
    except TimeoutException:
        LOGGER.info("Timeout waiting for login/checkout page. Current URL: " + driver.current_url)
        LOGGER.info("Page title: " + driver.title)
        # Continue anyway and try to find login elements

    # Check for various checkout page indicators
    checkout_indicators = [
        "//*[contains(text(),'Order Summary')]",
        "//*[contains(text(),'a payment method')]",
        "//*[contains(text(),'Place your order')]",
        "//*[contains(text(),'Payment method')]",
        "//*[contains(text(),'Review your order')]",
        "//*[contains(text(),'Checkout')]",
        "//*[contains(text(),'Place Your Order')]"
    ]
    
    is_checkout_page = False
    for indicator in checkout_indicators:
        if driver.find_elements(By.XPATH, indicator):
            LOGGER.info(f"Found checkout indicator: {indicator}")
            is_checkout_page = True
            break
    
    if not is_checkout_page:
        LOGGER.info("Not in checkout, attempting login...")
        
        if driver.find_elements(By.XPATH, "//*[contains(text(),'" + merchant.usr + "')]"):
            LOGGER.info("Found username on page, clicking it...")
            driver.find_element(By.XPATH, "//*[contains(text(),'" + merchant.usr + "')]").click()  # click username in case we're on the Switch Accounts page
            WebDriverWait(driver, 30).until(expected_conditions.element_to_be_clickable((By.ID, 'signInSubmit')))
            time.sleep(1 + random.random() * 2)

        if driver.find_elements(By.ID, 'ap_email') or driver.find_elements(By.ID, 'ap_email_login'):  # if first run, fill in email. If subsequent run, nothing to fill in
            LOGGER.info("Found email field, entering username...")
            try:
                # Try the new email field ID first
                if driver.find_elements(By.ID, 'ap_email_login'):
                    driver.find_element(By.ID, 'ap_email_login').send_keys(merchant.usr)
                else:
                    driver.find_element(By.ID, 'ap_email').send_keys(merchant.usr)
                time.sleep(1 + random.random() * 2)
                LOGGER.info("Username entered successfully")
            except ElementNotInteractableException:  # Sometimes this field is prefilled with Firstname Lastname and does not accept input
                LOGGER.info("Email field not interactable, skipping...")
                pass
        else:
            LOGGER.info("No email field found. Looking for alternative login elements...")
            # Try alternative login field selectors
            alternative_email_fields = driver.find_elements(By.XPATH, "//input[@type='email' or @name='email' or contains(@placeholder,'email') or contains(@placeholder,'Email')]")
            
            if alternative_email_fields:
                LOGGER.info("Found alternative email field, entering username...")
                try:
                    alternative_email_fields[0].send_keys(merchant.usr)
                    time.sleep(1 + random.random() * 2)
                    LOGGER.info("Username entered in alternative field")
                except:
                    LOGGER.info("Failed to enter username in alternative field")
            else:
                LOGGER.info("No email/username field found at all")

        if driver.find_elements(By.ID, 'continue') or driver.find_elements(By.XPATH, "//input[@aria-labelledby='continue-announce']"):  # a/b tested new UI flow
            # Try the new continue button first
            if driver.find_elements(By.XPATH, "//input[@aria-labelledby='continue-announce']"):
                driver.find_element(By.XPATH, "//input[@aria-labelledby='continue-announce']").click()
            else:
                driver.find_element(By.ID, 'continue').click()
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, 'ap_password')))
            time.sleep(1 + random.random() * 2)

        if driver.find_elements(By.NAME, 'rememberMe'):
            time.sleep(1 + random.random() * 2)
            driver.find_element(By.NAME, 'rememberMe').click()

        driver.find_element(By.ID, 'ap_password').send_keys(merchant.psw)
        time.sleep(1 + random.random() * 2)
        driver.find_element(By.ID, 'signInSubmit').click()
        time.sleep(1 + random.random() * 2)

        handle_anti_automation_challenge(driver, merchant)

        try:  # Push Notification / Email MFA
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'approve the notification')]")))
            if driver.find_elements(By.XPATH, "//*[contains(text(),'approve the notification')]"):
                LOGGER.info('\n')
                LOGGER.info('Please approve the Amazon login notification sent to your email or phone. Debbit will wait up to 3 minutes.')
                for i in range(180):  # Wait for up to 3 minutes for user to approve login notification
                    if not driver.find_elements(By.XPATH, "//*[contains(text(),'approve the notification')]"):
                        break
                    time.sleep(1)
        except TimeoutException:
            pass

        try:  # OTP text message
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'phone number ending in')]")))
            if driver.find_elements(By.ID, 'auth-mfa-remember-device'):
                driver.find_element(By.ID, 'auth-mfa-remember-device').click()

            sent_to_text = driver.find_element(By.XPATH, "//*[contains(text(),'phone number ending in')]").text
            LOGGER.info(sent_to_text)
            LOGGER.info('Enter OTP here:')
            otp = input()
            driver.find_element(By.ID, 'auth-mfa-otpcode').send_keys(otp)
            time.sleep(1 + random.random() * 2)
            driver.find_element(By.ID, 'auth-signin-button').click()
            time.sleep(1 + random.random() * 2)
        except TimeoutException:
            pass

        try:  # OTP email validation
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'One Time Pass')]")))
            otp_email = True
        except TimeoutException:
            otp_email = False

        try:
            driver.find_element(By.XPATH, "//*[contains(text(),'one-time pass')]").click()
            time.sleep(1 + random.random() * 2)
            otp_email = True
        except common.exceptions.NoSuchElementException:
            pass

        if otp_email:
            if driver.find_elements(By.ID, 'continue'):
                driver.find_element(By.ID, 'continue').click()
                time.sleep(1 + random.random() * 2)

            handle_anti_automation_challenge(driver, merchant)

            try:  # User may have manually advanced to gift card screen or stopped at OTP input. Handle OTP input if on OTP screen.
                WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Enter OTP')]")))
                sent_to_text = driver.find_element(By.XPATH, "//*[contains(text(),'@')]").text
                LOGGER.info(sent_to_text)
                LOGGER.info('Enter OTP here:')
                otp = input()
                # Try to find the OTP input field more specifically
                try:
                    # Look for OTP input field with more specific selectors
                    otp_input = driver.find_element(By.ID, 'auth-mfa-otpcode')
                except:
                    try:
                        # Try alternative selectors for OTP field
                        otp_input = driver.find_element(By.XPATH, "//input[@type='text' and @placeholder*='code']")
                    except:
                        try:
                            # Try any visible input field
                            otp_input = driver.find_element(By.XPATH, "//input[@type='text' and not(@type='hidden')]")
                        except:
                            # Fallback to first visible input
                            otp_input = driver.find_element(By.XPATH, "//input[not(@type='hidden')]")
                
                otp_input.send_keys(otp)
                time.sleep(1 + random.random() * 2)
                otp_input.send_keys(Keys.TAB)
                time.sleep(1 + random.random() * 2)
                otp_input.send_keys(Keys.ENTER)
                time.sleep(1 + random.random() * 2)
            except TimeoutException:
                pass

        try:
            WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Not now')]")))
            driver.find_element(By.XPATH, "//*[contains(text(),'Not now')]").click()
            time.sleep(1 + random.random() * 2)
        except TimeoutException:  # add mobile number page
            pass

    # Now expecting to be on checkout page with debit card selection present
    # Add debugging to see what page we're actually on
    LOGGER.info("Waiting for checkout page after OTP entry...")
    
    # First, let's wait a bit longer and check what page we're actually on
    time.sleep(5)  # Give the page more time to load
    
    # Check current page title and URL for debugging
    try:
        current_title = driver.title
        current_url = driver.current_url
        LOGGER.info(f"Current page title: {current_title}")
        LOGGER.info(f"Current page URL: {current_url}")
    except Exception as e:
        LOGGER.info(f"Could not get page info: {e}")
    
    # Try to find any common checkout page elements
    checkout_indicators = [
        "//*[contains(text(),'Order Summary')]",
        "//*[contains(text(),'a payment method')]",
        "//*[contains(text(),'Payment method')]",
        "//*[contains(text(),'Review your order')]",
        "//*[contains(text(),'Place your order')]",
        "//*[contains(text(),'Continue')]",
        "//*[contains(text(),'Checkout')]",
        "//*[contains(text(),'Review order')]",
        "//*[contains(text(),'Payment')]",
        "//*[contains(text(),'Card ending in')]"
    ]
    
    found_element = None
    for indicator in checkout_indicators:
        try:
            elements = driver.find_elements(By.XPATH, indicator)
            if elements:
                found_element = indicator
                LOGGER.info(f"Found checkout indicator: {indicator}")
                break
        except Exception:
            pass
    
    if not found_element:
        LOGGER.warning("No common checkout elements found, proceeding anyway...")
    
    # Try the original wait with more conditions
    try:
        WebDriverWait(driver, 30).until(utils.AnyExpectedCondition(
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Order Summary')]")),  # Checkout page
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'a payment method')]")),  # Another version of the checkout page
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Payment method')]")),  # Alternative payment method text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Review your order')]")),  # Review order page
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Place your order')]")),  # Place order button
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Continue')]")),  # Continue button
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Checkout')]")),  # Checkout text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Review order')]")),  # Review order text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Payment')]")),  # Payment text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Card ending in')]"))  # Card selection
        ))
        LOGGER.info("Successfully found checkout page elements")
    except TimeoutException:
        LOGGER.error("Timeout waiting for checkout page elements. Current page might be different than expected.")
        # Continue anyway and try to find payment elements

    # First, let's debug what payment elements are actually present
    LOGGER.info("Looking for payment method elements...")
    
    # Check if we need to expand the payment method dropdown
    dropdown_selectors = [
        (By.ID, 'payChangeButtonId'),
        (By.ID, 'payment-change-link'),
        (By.XPATH, "//*[contains(text(),'Change')]"),
        (By.XPATH, "//*[contains(text(),'Select payment method')]"),
        (By.XPATH, "//*[contains(text(),'Payment method')]"),
        (By.XPATH, "//*[contains(text(),'Choose payment')]")
    ]
    
    dropdown_clicked = False
    for selector_type, selector_value in dropdown_selectors:
        try:
            elements = driver.find_elements(selector_type, selector_value)
            if elements:
                LOGGER.info(f"Found dropdown element: {selector_type}:{selector_value}")
                for element in elements:
                    try:
                        time.sleep(1 + random.random() * 2)
                        element.click()
                        LOGGER.info(f"Clicked dropdown: {selector_type}:{selector_value}")
                        dropdown_clicked = True
                        
                        # Wait for the dropdown to fully expand and cards to load
                        LOGGER.info("Waiting for payment method dropdown to fully load...")
                        try:
                            # First wait for the loading text to disappear
                            WebDriverWait(driver, 15).until_not(
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading your payment information')]"))
                            )
                            LOGGER.info("Loading text disappeared, payment methods should be loaded")
                            
                            # Then wait for actual payment method elements to appear
                            WebDriverWait(driver, 10).until(utils.AnyExpectedCondition(
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'ending in')]")),
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'Visa')]")),
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'Mastercard')]")),
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'American Express')]")),
                                expected_conditions.presence_of_element_located((By.XPATH, "//*[contains(text(),'Discover')]"))
                            ))
                            LOGGER.info("Payment method dropdown loaded successfully")
                        except TimeoutException:
                            LOGGER.warning("Timeout waiting for dropdown to load, continuing anyway...")
                        
                        break
                    except WebDriverException as e:
                        LOGGER.debug(f"Failed to click dropdown {selector_type}:{selector_value}: {e}")
                        pass
                if dropdown_clicked:
                    break
        except Exception as e:
            LOGGER.debug(f"Dropdown selector {selector_type}:{selector_value} failed: {e}")
            pass
    
    # Now try to find and select the specific card
    LOGGER.info(f"Looking for card ending in {merchant.card[-4:]}...")
    
    # First, let's see what cards are actually available
    LOGGER.info("Checking what cards are available in the dropdown...")
    available_card_selectors = [
        "//*[contains(text(),'ending in')]",
        "//*[contains(text(),'Card ending in')]",
        "//*[contains(text(),'••••')]",
        "//*[contains(text(),'****')]",
        "//*[contains(text(),'Visa')]",
        "//*[contains(text(),'Mastercard')]",
        "//*[contains(text(),'American Express')]",
        "//*[contains(text(),'Discover')]",
        f"//*[contains(text(),'{merchant.card[-4:]}')]",  # Look for the specific card number
        "//*[contains(text(),'card')]",  # Look for any card-related text
        "//*[contains(text(),'Card')]",
        "//*[contains(text(),'payment')]",  # Look for payment-related text
        "//*[contains(text(),'Payment')]"
    ]
    
    # More comprehensive debugging to see all elements
    LOGGER.info("=== COMPREHENSIVE CARD SEARCH ===")
    
    # First, let's get ALL text elements in the dropdown area
    all_text_elements = driver.find_elements(By.XPATH, "//*[text()]")
    LOGGER.info(f"Found {len(all_text_elements)} total text elements")
    
    # Show all elements with substantial text
    for i, element in enumerate(all_text_elements[:50]):  # Show first 50 elements
        try:
            element_text = element.text.strip()
            if element_text and len(element_text) > 3:  # Show elements with more than 3 characters
                LOGGER.info(f"  All Element {i}: '{element_text}'")
        except:
            pass
    
    # Now check our specific selectors
    for selector in available_card_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                LOGGER.info(f"Found {len(elements)} elements with selector: {selector}")
                for i, element in enumerate(elements[:15]):  # Show first 15 elements
                    try:
                        element_text = element.text.strip()
                        if element_text and len(element_text) > 3:  # Show elements with more than 3 characters
                            LOGGER.info(f"  Element {i}: '{element_text}'")
                    except:
                        pass
        except Exception as e:
            LOGGER.debug(f"Available card selector {selector} failed: {e}")
            pass
    
    card_selectors = [
        f"//span[contains(text(),'ending in {merchant.card[-4:]}')]",
        f"//*[contains(text(),'ending in {merchant.card[-4:]}')]",
        f"//div[contains(text(),'ending in {merchant.card[-4:]}')]",
        f"//*[contains(text(),'{merchant.card[-4:]}')]",
        f"//*[contains(text(),'Card ending in {merchant.card[-4:]}')]",
        f"//*[contains(text(),'ending in {merchant.card[-4:]}')]",
        f"//*[contains(text(),'•••• {merchant.card[-4:]}')]",  # Masked card format
        f"//*[contains(text(),'**** {merchant.card[-4:]}')]",  # Another masked format
        f"//*[contains(text(),'*{merchant.card[-4:]}')]",  # Single asterisk format
        f"//*[contains(text(),'•{merchant.card[-4:]}')]",  # Single bullet format
        f"//*[contains(text(),'Visa ending in {merchant.card[-4:]}')]",  # Visa specific
        f"//*[contains(text(),'Mastercard ending in {merchant.card[-4:]}')]",  # Mastercard specific
        f"//*[contains(text(),'American Express ending in {merchant.card[-4:]}')]",  # Amex specific
        f"//*[contains(text(),'Discover ending in {merchant.card[-4:]}')]",  # Discover specific
        f"//*[contains(text(),'Visa •••• {merchant.card[-4:]}')]",  # Visa with bullets
        f"//*[contains(text(),'Mastercard •••• {merchant.card[-4:]}')]",  # Mastercard with bullets
        f"//*[contains(text(),'Amex •••• {merchant.card[-4:]}')]",  # Amex with bullets
        f"//*[contains(text(),'Discover •••• {merchant.card[-4:]}')]"  # Discover with bullets
    ]
    
    card_selected = False
    for selector in card_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            LOGGER.info(f"Found {len(elements)} elements for selector: {selector}")
            for i, element in enumerate(elements):
                try:
                    # Get element text for debugging
                    element_text = element.text
                    LOGGER.info(f"Element {i} text: '{element_text}'")
                    
                    time.sleep(1 + random.random() * 2)
                    element.click()
                    card_selected = True
                    LOGGER.info(f"Successfully selected card using selector: {selector}")
                    break
                except WebDriverException as e:
                    LOGGER.debug(f"Failed to click element {i} with selector {selector}: {e}")
                    pass
            if card_selected:
                break
        except Exception as e:
            LOGGER.debug(f"Card selector {selector} failed: {e}")
            pass

    if not card_selected:
        raise Exception('Unable to find or unable to click on card that has last 4 digits matching config file card. This prevents charging the wrong card.')

    # After selecting the card, click "Use this payment method" to confirm the selection
    LOGGER.info("Card selected successfully. Now clicking 'Use this payment method'...")
    
    use_payment_method_selectors = [
        (By.ID, 'orderSummaryPrimaryActionBtn'),
        (By.XPATH, "//*[contains(text(),'Use this payment method')]"),
        (By.XPATH, "//*[contains(text(),'Use payment method')]"),
        (By.XPATH, "//*[contains(text(),'Confirm payment')]"),
        (By.XPATH, "//*[contains(text(),'Continue')]"),
        (By.XPATH, "//*[contains(text(),'Next')]"),
        (By.XPATH, "//*[contains(text(),'Proceed')]")
    ]
    
    payment_method_confirmed = False
    for selector_type, selector_value in use_payment_method_selectors:
        try:
            elements = driver.find_elements(selector_type, selector_value)
            if elements:
                LOGGER.info(f"Found {len(elements)} 'Use payment method' elements with: {selector_type}:{selector_value}")
                for element in elements:
                    try:
                        # Try multiple click methods
                        time.sleep(1 + random.random() * 2)
                        
                        # Method 1: Regular click
                        try:
                            element.click()
                            LOGGER.info(f"Clicked payment method confirmation: {selector_type}:{selector_value}")
                            payment_method_confirmed = True
                            break
                        except WebDriverException:
                            pass
                        
                        # Method 2: JavaScript click
                        try:
                            driver.execute_script("arguments[0].click();", element)
                            LOGGER.info(f"JavaScript clicked payment method confirmation: {selector_type}:{selector_value}")
                            payment_method_confirmed = True
                            break
                        except WebDriverException:
                            pass
                        
                        # Method 3: Scroll into view and click
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.5)
                            element.click()
                            LOGGER.info(f"Scrolled and clicked payment method confirmation: {selector_type}:{selector_value}")
                            payment_method_confirmed = True
                            break
                        except WebDriverException:
                            pass
                        
                        # Method 4: Try clicking parent element
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            parent.click()
                            LOGGER.info(f"Clicked parent of payment method confirmation: {selector_type}:{selector_value}")
                            payment_method_confirmed = True
                            break
                        except WebDriverException:
                            pass
                            
                    except WebDriverException as e:
                        LOGGER.debug(f"Failed to click payment method element: {e}")
                        pass
                if payment_method_confirmed:
                    break
        except Exception as e:
            LOGGER.debug(f"Payment method selector {selector_type}:{selector_value} failed: {e}")
            pass
    
    if not payment_method_confirmed:
        LOGGER.warning("Could not find or click 'Use this payment method' button. Trying alternative buttons...")
        # Try other common button texts
        alternative_buttons = [
            "//*[contains(text(),'Next')]",
            "//*[contains(text(),'Proceed')]",
            "//*[contains(text(),'Submit')]",
            "//*[contains(text(),'Confirm')]",
            "//*[contains(text(),'Place order')]"
        ]
        
        for button_xpath in alternative_buttons:
            try:
                elements = driver.find_elements(By.XPATH, button_xpath)
                for element in elements:
                    try:
                        time.sleep(1 + random.random() * 2)
                        element.click()
                        LOGGER.info(f"Clicked alternative button: {button_xpath}")
                        payment_method_confirmed = True
                        break
                    except WebDriverException:
                        pass
                if payment_method_confirmed:
                    break
            except Exception:
                pass

    # After card selection, let's see what's on the page
    LOGGER.info("Card selected successfully. Checking what elements are now available...")
    
    # Check for various possible next steps
    next_step_selectors = [
        (By.ID, 'submitOrderButtonId'),
        (By.ID, 'placeYourOrder'),
        (By.XPATH, "//*[contains(text(),'Place your order')]"),
        (By.XPATH, "//*[contains(text(),'Place Your Order')]"),
        (By.XPATH, "//*[contains(text(),'Continue')]"),
        (By.XPATH, "//*[contains(text(),'Use this payment method')]"),
        (By.XPATH, "//*[contains(text(),'Review your order')]"),
        (By.XPATH, f"//input[@placeholder='ending in {merchant.card[-4:]}']")
    ]
    
    for selector_type, selector_value in next_step_selectors:
        try:
            elements = driver.find_elements(selector_type, selector_value)
            if elements:
                LOGGER.info(f"Found {len(elements)} elements for: {selector_type}:{selector_value}")
                for i, element in enumerate(elements[:3]):  # Show first 3 elements
                    try:
                        element_text = element.text.strip()
                        if element_text:
                            LOGGER.info(f"  Element {i}: '{element_text}'")
                    except:
                        pass
        except Exception as e:
            LOGGER.debug(f"Next step selector {selector_type}:{selector_value} failed: {e}")
            pass
    
    # Now wait for the expected elements
    try:
        WebDriverWait(driver, 10).until(utils.AnyExpectedCondition(
            expected_conditions.element_to_be_clickable((By.ID, 'submitOrderButtonId')),  # "Place your order" button showing, card ready to be used
            expected_conditions.element_to_be_clickable((By.ID, 'placeYourOrder')),  # Other checkout page "Place your order" button showing, card ready to be used
            expected_conditions.element_to_be_clickable((By.XPATH, "//input[@placeholder='ending in " + merchant.card[-4:] + "']")),  # Verify card flow
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Place your order')]")),  # Place your order text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Place Your Order')]")),  # Place Your Order text
            expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Continue')]"))  # Continue button
        ))
        LOGGER.info("Found expected next step elements")
    except TimeoutException:
        LOGGER.error("Timeout waiting for next step elements after card selection")
        # Continue anyway and try to find what's available

    if driver.find_elements(By.XPATH, "//input[@placeholder='ending in " + merchant.card[-4:] + "']"):  # Verify card flow
        elem = driver.find_element(By.XPATH, "//input[@placeholder='ending in " + merchant.card[-4:] + "']")
        time.sleep(1 + random.random() * 2)
        elem.send_keys(merchant.card)
        time.sleep(1 + random.random() * 2)
        elem.send_keys(Keys.TAB)
        time.sleep(1 + random.random() * 2)
        elem.send_keys(Keys.ENTER)

        time.sleep(10 + random.random() * 2)
        if driver.find_elements(By.ID, 'orderSummaryPrimaryActionBtn'):
            driver.find_element(By.ID, 'orderSummaryPrimaryActionBtn').click()  # Click "Use this payment method" button
        else:  # Find Continue text, the grandparent element of the text is the clickable Continue button
            driver.find_element(By.XPATH, "//span[contains(text(),'Continue')]").find_element(By.XPATH, '../..').click()

        WebDriverWait(driver, 10).until(utils.AnyExpectedCondition(
            expected_conditions.element_to_be_clickable((By.ID, 'submitOrderButtonId')),  # "Place your order" button showing, card ready to be used
            expected_conditions.element_to_be_clickable((By.ID, 'placeYourOrder')),  # Other checkout page "Place your order" button showing, card ready to be used
        ))

    time.sleep(1 + random.random() * 2)

    if not is_order_total_correct(driver, amount):
        return Result.unverified

    # Try to find and click the "Place your order" button
    place_order_selectors = [
        (By.ID, 'submitOrderButtonId'),
        (By.ID, 'placeYourOrder'),
        (By.XPATH, "//*[contains(text(),'Place your order')]"),
        (By.XPATH, "//*[contains(text(),'Place Your Order')]"),
        (By.XPATH, "//*[contains(text(),'Place Order')]"),
        (By.XPATH, "//*[contains(text(),'Complete purchase')]"),
        (By.XPATH, "//*[contains(text(),'Buy now')]")
    ]
    
    order_placed = False
    for selector_type, selector_value in place_order_selectors:
        try:
            elements = driver.find_elements(selector_type, selector_value)
            if elements:
                LOGGER.info(f"Found {len(elements)} place order elements with: {selector_type}:{selector_value}")
                for element in elements:
                    try:
                        time.sleep(1 + random.random() * 2)
                        element.click()
                        LOGGER.info(f"Clicked place order button: {selector_type}:{selector_value}")
                        order_placed = True
                        break
                    except WebDriverException as e:
                        LOGGER.debug(f"Failed to click place order element: {e}")
                        pass
                if order_placed:
                    break
        except Exception as e:
            LOGGER.debug(f"Place order selector {selector_type}:{selector_value} failed: {e}")
            pass
    
    if not order_placed:
        raise Exception('Unable to find or click "Place your order" button after card selection.')

    # Wait for order confirmation with more comprehensive success indicators
    LOGGER.info("Waiting for order confirmation...")
    
    success_indicators = [
        "//*[contains(text(),'your order has been placed')]",
        "//*[contains(text(),'Order placed')]",
        "//*[contains(text(),'Order confirmation')]",
        "//*[contains(text(),'Thank you for your order')]",
        "//*[contains(text(),'Your order has been confirmed')]",
        "//*[contains(text(),'Order received')]",
        "//*[contains(text(),'Order confirmed')]",
        "//*[contains(text(),'Successfully placed')]",
        "//*[contains(text(),'Order number')]",
        "//*[contains(text(),'Order #')]",
        "//*[contains(text(),'confirmation email')]",
        "//*[contains(text(),'email confirmation')]",
        "//*[contains(text(),'Thank you')]",
        "//*[contains(text(),'Order summary')]"
    ]
    
    try:
        # Wait for any success indicator to appear
        WebDriverWait(driver, 30).until(utils.AnyExpectedCondition(
            *[expected_conditions.presence_of_element_located((By.XPATH, indicator)) for indicator in success_indicators]
        ))
        LOGGER.info("Order confirmation detected")
        
        # Check which success indicator was found
        for indicator in success_indicators:
            if driver.find_elements(By.XPATH, indicator):
                LOGGER.info(f"Found success indicator: {indicator}")
                return Result.success
                
        return Result.success  # If we got here, some indicator was found
        
    except TimeoutException:
        LOGGER.error('Clicked "Place your order" button, but unable to confirm if order was successful.')
        LOGGER.info("Checking current page for any success indicators...")
        
        # Check what's actually on the page
        for indicator in success_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements:
                    LOGGER.info(f"Found success indicator after timeout: {indicator}")
                    return Result.success
            except Exception:
                pass
        
        # If no success indicators found, check if we're on a different page
        current_url = driver.current_url
        current_title = driver.title
        LOGGER.info(f"Current URL after order placement: {current_url}")
        LOGGER.info(f"Current page title: {current_title}")
        
        # Check for various success conditions
        if "checkout" not in current_url.lower() and "order" in current_url.lower():
            LOGGER.info("Redirected to order page, assuming success")
            return Result.success
        elif "/pay" in current_url.lower():
            LOGGER.info("Redirected to payment confirmation page, assuming success")
            return Result.success
        elif "confirmation" in current_url.lower():
            LOGGER.info("Redirected to confirmation page, assuming success")
            return Result.success
        elif "thank" in current_title.lower():
            LOGGER.info("Thank you page detected, assuming success")
            return Result.success
        elif "order" in current_title.lower() and "checkout" not in current_title.lower():
            LOGGER.info("Order page detected, assuming success")
            return Result.success
            
        return Result.unverified


def handle_anti_automation_challenge(driver, merchant):
    try:
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(),'nter the characters')]")))

        time.sleep(1 + random.random() * 2)
        if driver.find_elements(By.ID, 'ap_password'):
            driver.find_element(By.ID, 'ap_password').send_keys(merchant.psw)

        LOGGER.info('amazon captcha detected')
        input('''
Anti-automation captcha detected. Please follow these steps, future runs shouldn't need captcha input unless you set "use_cookies: no" in config.txt.

1. Open the Firefox window that debbit created.
2. Input the captcha / other anti-automation challenges.
3. You should now be on the gift card reload page
4. Click on this terminal window and hit "Enter" to continue running debbit.
''')
    except TimeoutException:
        pass


def is_order_total_correct(driver, amount):
    elements_to_check = []

    # Try various possible order total selectors
    total_selectors = [
        (By.ID, 'subtotals-marketplace-spp-bottom'),
        (By.CLASS_NAME, 'grand-total-price'),
        (By.XPATH, "//*[contains(text(),'Total')]"),
        (By.XPATH, "//*[contains(text(),'Order total')]"),
        (By.XPATH, "//*[contains(text(),'Total (1 item)')]"),
        (By.XPATH, "//*[contains(text(),'Total (1 item)')]"),
        (By.XPATH, "//*[contains(text(),'$5.00')]"),  # Look for the specific amount
        (By.XPATH, "//*[contains(text(),'$5.00')]"),
        (By.XPATH, "//*[contains(text(),'5.00')]"),
        (By.XPATH, "//*[contains(text(),'5.00')]"),
        (By.XPATH, "//*[contains(text(),'Total:')]"),
        (By.XPATH, "//*[contains(text(),'Total:')]"),
        (By.XPATH, "//*[contains(text(),'Order Summary')]"),
        (By.XPATH, "//*[contains(text(),'Order Summary')]"),
        (By.XPATH, "//*[contains(text(),'Review your order')]"),
        (By.XPATH, "//*[contains(text(),'Review your order')]")
    ]

    for selector_type, selector_value in total_selectors:
        try:
            elements = driver.find_elements(selector_type, selector_value)
            for element in elements:
                text = element.text
                if text and text.strip():
                    elements_to_check.append(text)
                    LOGGER.debug(f"Found potential total element: {text}")
        except Exception as e:
            LOGGER.debug(f"Selector {selector_type}:{selector_value} failed: {e}")
            pass

    expected_order_total = '$' + utils.cents_to_str(amount)
    LOGGER.info(f"Looking for expected total: {expected_order_total}")
    LOGGER.info(f"Found elements to check: {elements_to_check}")
    
    for element in elements_to_check:
        if expected_order_total in element:
            LOGGER.info(f"Found matching total: {element}")
            return True

    LOGGER.error('Unable to verify order total is correct, not purchasing. Could not find expected amount ' + expected_order_total + ' in ' + str(elements_to_check))
    return False
