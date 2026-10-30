"""Unit tests for live browser visibility improvements, anti-looping, and semantic verification."""

import pytest
from blindspot.ai.providers.antigravity import AntigravityProvider, _is_carousel_or_sponsored
from blindspot.execution.agent import PersonaTaskAgent
from blindspot.execution.models import ActionType, AgentAction
from blindspot.personas.models import PersonaTask


def test_carousel_filter_identifies_sponsored_and_ad_elements():
    """Verify sponsored carousels and ad tiles are accurately detected and isolated."""
    assert _is_carousel_or_sponsored('href="/apple-iphone-13/p/itm123?marketplace=FLIPKART&p2psimilar=true"') is True
    assert _is_carousel_or_sponsored('[css:div.carousel-container > a.item]') is True
    assert _is_carousel_or_sponsored('aria-label="Sponsored recommendation tile"') is True
    assert _is_carousel_or_sponsored('Similar products you may also like') is True
    assert _is_carousel_or_sponsored('href="/apple-iphone-16-black-128-gb/p/itmabc"') is False
    assert _is_carousel_or_sponsored('<button> Add to Cart </button>') is False


def test_semantic_cart_verification_with_stop_words():
    """Verify criteria like 'Cart page opened; checkout button displayed' succeed via stop-word filtering and semantic cart rules."""
    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_cart",
        objective="Add item to shopping cart and verify checkout button",
        success_criteria=["Cart page opened; checkout button displayed"],
        evidence_to_collect=["Cart evidence"],
    )

    # 1. Test via semantic cart URL
    satisfied, reason = agent._verify_criteria_on_page(
        task=task,
        url="https://www.flipkart.com/viewcart?exploreMode=true",
        page_text="My Cart (1 item) Place Order Total Amount ₹69,990",
    )
    assert satisfied is True
    assert "shopping cart" in reason.lower()

    # 2. Test via semantic cart text on generic URL
    satisfied2, reason2 = agent._verify_criteria_on_page(
        task=task,
        url="https://example.com/checkout/summary",
        page_text="Your shopping cart summary: 1 item. Place order to complete purchase.",
    )
    assert satisfied2 is True

    # 3. Test that stop-words (opened, displayed) don't prevent match when core keywords match
    task2 = PersonaTask(
        id="task_checkout",
        objective="Verify checkout button presence",
        success_criteria=["checkout button displayed"],
        evidence_to_collect=["Checkout evidence"],
    )
    satisfied3, reason3 = agent._verify_criteria_on_page(
        task=task2,
        url="https://example.com/cart",
        page_text="Proceed to checkout button on screen",
    )
    assert satisfied3 is True


def test_variant_click_throttling_and_carousel_isolation():
    """Verify agent does not click into recommendation carousels and caps variant clicks to 1."""
    provider = AntigravityProvider()

    # Scenario: On PDP with an ad carousel containing a 128 GB link, and the primary Add to Cart button
    prompt = """
Objective: Search Apple iPhone 16 and add to cart
URL: https://www.flipkart.com/apple-iphone-16-128-gb/p/itm123
Step 1: fill @e1 with "Apple iPhone 16"
Step 2: click @e5 to select top listing

Elements on page:
@e10 <a> (link) "Apple iPhone 13 (Blue, 128 GB) [href:/apple-iphone-13/p/itm456?p2psimilar=true]"
@e11 <button> (button) "Add to Cart" [css:button._2KpZ6l._2U9uOA]
@e12 <button> (button) "Buy Now"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    # Must choose @e11 (Add to Cart), NOT @e10 (the sponsored 128 GB carousel)
    assert action.action == ActionType.CLICK
    assert action.target == "@e10" or action.target == "@e11"
    assert action.target == "@e11"  # Directly Add to Cart!


def test_out_of_stock_backoff_navigation():
    """Verify that an unavailable product triggers GO_BACK after variants are exhausted."""
    provider = AntigravityProvider()

    # Scenario: Product is out of stock, variant was already clicked once in Step 3
    prompt = """
Objective: Search Apple iPhone 16 and add to cart
URL: https://www.flipkart.com/apple-iphone-16-desert-512-gb/p/itm999
Step 1: fill @e1 with "Apple iPhone 16"
Step 2: click @e5 to select top listing
Step 3: click product variant chip @e8 (256 GB)

Elements on page:
@e1 <button> (button) "Currently unavailable"
@e2 <div> (text) "This item is out of stock"
@e3 <button> (button) "Notify Me"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    # Must execute GO_BACK to search results to pick an available item
    assert action.action == ActionType.GO_BACK
    assert "out of stock" in action.reasoning.lower() or "search results" in action.reasoning.lower()


def test_product_search_bar_selection_rejects_location_and_flight_inputs():
    """Verify that location, pincode, city, and flight inputs are rejected in favor of product search."""
    provider = AntigravityProvider()

    prompt = """
Objective: Locate the search bar, search for 'Apple iPhone 16', and browse result listings
URL: https://www.flipkart.com/
Elements on page:
@e1 <input> (text) placeholder="Enter delivery pincode" [css:input._166D2F]
@e2 <input> (text) placeholder="Search for your city or location"
@e3 <input> (text) name="q" placeholder="Search for Products, Brands and More" title="Search for Products, Brands and More"
@e4 <button> (button) "Search"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    assert action.action == ActionType.FILL
    assert action.target == "@e3"  # Primary product search bar, NOT @e1 or @e2!
    assert "iphone 16" in (action.value or action.text or "").lower()


def test_flight_and_travel_recovery():
    """Verify that if browser navigates to flight booking or sub-vertical, agent triggers GO_BACK immediately."""
    provider = AntigravityProvider()

    prompt = """
Objective: Search Apple iPhone 16 and add to cart
URL: https://www.flipkart.com/travel/flights
Elements on page:
@e1 <input> (text) placeholder="Enter Departure City"
@e2 <input> (text) placeholder="Enter Destination City"
@e3 <button> (button) "Search Flights"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    assert action.action == ActionType.GO_BACK
    assert "flight" in action.reasoning.lower() or "shopping" in action.reasoning.lower()


def test_navigation_skips_flight_booking_links():
    """Verify that general exploration ignores flight booking and irrelevant category links."""
    provider = AntigravityProvider()

    prompt = """
Objective: Explore primary navigation links
URL: https://www.flipkart.com/
Elements on page:
@e1 <a> (link) text="Flight Bookings" href="/travel/flights"
@e2 <a> (link) text="Grocery" href="/grocery"
@e3 <a> (link) text="Mobiles" href="/mobiles"
@e4 <a> (link) text="Electronics" href="/electronics"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    assert action.action == ActionType.CLICK
    assert action.target not in ("@e1", "@e2")
    assert action.target in ("@e3", "@e4")


def test_dynamic_persona_generation_inherits_user_context(tmp_path):
    """Verify generate_personas_and_tasks without --personas-file synthesizes Elena with user target context."""
    from blindspot.personas.generator import generate_personas_and_tasks
    from blindspot.runtime import BrowserInspectionResult, InspectionSummary, ViewportSize

    provider = AntigravityProvider()
    inspection = BrowserInspectionResult(
        timestamp="2026-10-30T12:00:00Z",
        requested_url="https://www.flipkart.com",
        final_url="https://www.flipkart.com/",
        context="Search Apple iPhone 16 and add to cart",
        title="Flipkart",
        viewport=ViewportSize(width=1280, height=800),
        browser="chromium",
        screenshot_path=str(tmp_path / "shot.png"),
        result_json_path=str(tmp_path / "res.json"),
        summary=InspectionSummary(total_interactive_elements=10, links_count=8, buttons_count=1, form_fields_count=1, text_length=150),
        interactive_elements=[],
        page_text="Flipkart online store",
    )

    plan = generate_personas_and_tasks(
        inspection_result=inspection,
        provider=provider,
        num_personas=1,
    )
    assert len(plan.personas) == 1
    elena = plan.personas[0]
    assert "Elena" in elena.name
    # Elena's tasks must be customized to the target product
    assert any("iphone 16" in t.objective.lower() for t in elena.tasks)
    assert any("cart" in t.objective.lower() for t in elena.tasks)


def test_auth_barrier_requests_prompt_user():
    """Verify that encountering an OTP or login prompt during an e-commerce task returns <PROMPT_USER>."""
    provider = AntigravityProvider()

    prompt = """
Objective: Navigate to the Cart and proceed to checkout
URL: https://www.flipkart.com/checkout/init
Elements on page:
@e1 <input> (text) placeholder="Enter 6-digit OTP"
@e2 <button> (button) "Verify"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    assert action.action == ActionType.FILL
    assert action.target == "@e1"
    assert action.value == "<PROMPT_USER>"
    assert "terminal" in action.reasoning.lower() or "prompt" in action.reasoning.lower()


def test_lost_navigation_triggers_go_back_instead_of_giving_up():
    """Verify that when the agent is lost or cannot find target actions after scrolling, it uses GO_BACK instead of giving up."""
    provider = AntigravityProvider()

    prompt = """
Objective: Search Apple iPhone 16 and add to cart
URL: https://www.flipkart.com/some-unexpected-subpage
Step 1: fill @e1 with "Apple iPhone 16"
Step 2: press Enter to execute search
Step 3: scroll down
Step 4: scroll down

Elements on page:
@e1 <div> (text) "No matching results found in this section"
@e2 <footer> (footer) "Copyright 2026"
"""
    action: AgentAction = provider.generate_structured(prompt=prompt, schema=AgentAction)

    # Must execute GO_BACK to re-orient, never ActionType.FINISH giving up early!
    assert action.action == ActionType.GO_BACK
    assert "back" in action.reasoning.lower()


def test_criteria_verification_succeeds_on_search_results():
    """Verify that search results page with results verifies Task 1 criteria without being blocked by words like 'query' or 'legible'."""
    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_search_and_discover",
        objective="Locate the search bar using high-contrast input, search for 'Apple iPhone 16', and browse result listings with legible text and prices.",
        success_criteria=[
            "Search query 'Apple iPhone 16' submitted",
            "Product search results displayed with legible titles and prices",
        ],
        evidence_to_collect=["Search input value", "Results heading text"],
    )

    satisfied, reason = agent._verify_criteria_on_page(
        task=task,
        url="https://www.flipkart.com/search?q=Apple+iPhone+16&otracker=search",
        page_text="Showing 1 – 24 of 1,200 results for 'Apple iPhone 16' Filters Sort By Apple iPhone 16 (Black, 128 GB) ₹69,990",
    )
    assert satisfied is True
    assert "search" in reason.lower()


def test_search_query_must_match_requested_product():
    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_search",
        objective="Search for 'Apple iPhone 16' and browse results",
        success_criteria=["Search query 'Apple iPhone 16' submitted", "Product search results displayed"],
        evidence_to_collect=[],
    )
    satisfied, _ = agent._verify_criteria_on_page(
        task, "https://www.flipkart.com/search?q=Apple+iPhone", "Showing 1 - 24 results Filters Sort By",
    )
    assert satisfied is False


def test_product_page_does_not_satisfy_add_to_cart():
    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_cart",
        objective="Open product details and add to cart",
        success_criteria=["Add to Cart or Buy Now clicked"],
        evidence_to_collect=[],
    )
    satisfied, _ = agent._verify_criteria_on_page(
        task,
        "https://www.flipkart.com/apple-iphone-16/p/itm123",
        "Apple iPhone 16 Specifications Add to Cart Buy Now",
    )
    assert satisfied is False


def test_active_tab_is_not_keyboard_tab_task():
    provider = AntigravityProvider()
    prompt = '''Objective: Open the top 'Apple iPhone 16' item in active tab, inspect specifications, and add to cart.
URL: https://www.flipkart.com/search?q=Apple+iPhone+16
Step 1: scroll down
Elements on page:
@e1 <a> (link) text="Apple iPhone 16 (128 GB)" href="/apple-iphone-16-128-gb/p/itm123"
'''
    action = provider._synthesize_agent_action(prompt, AgentAction)
    assert action.action == ActionType.CLICK
    assert action.target == "@e1"


def test_product_url_with_search_query_is_still_product_page():
    provider = AntigravityProvider()
    prompt = '''Objective: Navigate to the Cart, verify item details, and proceed to checkout.
URL: https://www.flipkart.com/apple-iphone-16-plus-black-128-gb/p/itm123?pid=123&q=Apple+iPhone+16
Elements on page:
@e1 <button> (button) text="Add to Cart"
@e2 <a> (link) text="Oppo F35 5G (Wave Blue, 128 GB) ₹62,999" href="/oppo-f35/p/itm456?fm=advertisement&p2psimilar=true"
'''
    action = provider._synthesize_agent_action(prompt, AgentAction)
    assert action.action == ActionType.CLICK
    assert action.target == "@e1"


def test_search_input_named_q_does_not_trigger_login_prompt():
    provider = AntigravityProvider()
    prompt = '''Objective: Search Apple iPhone 16 and add to cart
URL: https://www.flipkart.com/
Elements on page:
@e1 <input> (text) name="q" placeholder="Search for Products, Brands and More" [css:div.mobile-search]
'''
    action = provider._synthesize_agent_action(prompt, AgentAction)
    assert action.action == ActionType.FILL
    assert action.target == "@e1"
    assert action.value == "Apple iPhone 16"


def test_checkout_form_filling_and_order_submission():
    """Verify that provider systematically fills checkout form fields and clicks place order."""
    provider = AntigravityProvider()

    # Step 1: On checkout page with name, phone, address, city unfilled
    prompt_step1 = '''Objective: Complete checkout and place order
URL: http://127.0.0.1:8080/#checkout
Elements on page:
@e1 <input> (text) placeholder="Full name" [css:input#name]
@e2 <input> (tel) placeholder="10-digit mobile number" [css:input#phone]
@e3 <textarea> (textarea) placeholder="Delivery address" [css:textarea#address]
@e4 <input> (text) placeholder="City" [css:input#city]
@e5 <button> (button) "Place demo order · ₹70"
'''
    act1 = provider._synthesize_agent_action(prompt_step1, AgentAction)
    assert act1.action == ActionType.FILL
    assert act1.target == "@e1"
    assert "elena" in act1.value.lower()

    # Step 2: After name is filled, fill phone
    prompt_step2 = '''Objective: Complete checkout and place order
URL: http://127.0.0.1:8080/#checkout
Step 1: fill @e1 with "Elena Rostova"
Elements on page:
@e1 <input> (text) placeholder="Full name" [css:input#name]
@e2 <input> (tel) placeholder="10-digit mobile number" [css:input#phone]
@e3 <textarea> (textarea) placeholder="Delivery address" [css:textarea#address]
@e4 <input> (text) placeholder="City" [css:input#city]
@e5 <button> (button) "Place demo order · ₹70"
'''
    act2 = provider._synthesize_agent_action(prompt_step2, AgentAction)
    assert act2.action == ActionType.FILL
    assert act2.target == "@e2"
    assert "9876543210" in act2.value

    # Step 3: After name and phone filled, fill address
    prompt_step3 = '''Objective: Complete checkout and place order
URL: http://127.0.0.1:8080/#checkout
Step 1: fill @e1 with "Elena Rostova"
Step 2: fill @e2 with "9876543210"
Elements on page:
@e1 <input> (text) placeholder="Full name" [css:input#name]
@e2 <input> (tel) placeholder="10-digit mobile number" [css:input#phone]
@e3 <textarea> (textarea) placeholder="Delivery address" [css:textarea#address]
@e4 <input> (text) placeholder="City" [css:input#city]
@e5 <button> (button) "Place demo order · ₹70"
'''
    act3 = provider._synthesize_agent_action(prompt_step3, AgentAction)
    assert act3.action == ActionType.FILL
    assert act3.target == "@e3"
    assert "market street" in act3.value.lower()

    # Step 4: After all fields filled, clicks place demo order
    prompt_step4 = '''Objective: Complete checkout and place order
URL: http://127.0.0.1:8080/#checkout
Step 1: fill @e1 with "Elena Rostova"
Step 2: fill @e2 with "9876543210"
Step 3: fill @e3 with "124 Market Street, Apt 4B"
Step 4: fill @e4 with "Kolkata"
Elements on page:
@e1 <input> (text) placeholder="Full name" [css:input#name]
@e2 <input> (tel) placeholder="10-digit mobile number" [css:input#phone]
@e3 <textarea> (textarea) placeholder="Delivery address" [css:textarea#address]
@e4 <input> (text) placeholder="City" [css:input#city]
@e5 <button> (button) "Place demo order · ₹70"
'''
    act4 = provider._synthesize_agent_action(prompt_step4, AgentAction)
    assert act4.action == ActionType.CLICK
    assert act4.target == "@e5"


def test_destructive_action_guard_allows_demo_and_local_orders():
    """Verify is_action_destructive allows demo orders and local testing while blocking deletions."""
    from blindspot.execution.safety import is_action_destructive

    # Real purchases on live external domains are blocked
    is_dest, reason = is_action_destructive("Place Order", "")
    assert is_dest is True

    # Demo orders are allowed
    is_demo_dest, _ = is_action_destructive("Place demo order · ₹70", "")
    assert is_demo_dest is False

    # Purchases with allow_local=True are allowed
    is_local_dest, _ = is_action_destructive("Place Order", "", allow_local=True)
    assert is_local_dest is False

    # True destructive account deletion is blocked even locally
    is_wipe_dest, _ = is_action_destructive("Delete Account", "", allow_local=True)
    assert is_wipe_dest is True


def test_ux_evaluation_task_criteria_verification():
    """Verify that qualitative UX inspection tasks succeed upon completion."""
    agent = PersonaTaskAgent(provider=AntigravityProvider(), headless=True)
    task = PersonaTask(
        id="task_readability",
        objective="Inspect main navigation links and section headings to verify they are easy to find and readable",
        success_criteria=[
            "Primary navigation links and section headings are clearly identified",
            "Text contrast and font sizing meet readability expectations",
        ],
        evidence_to_collect=["Readability evidence"],
    )
    satisfied, reason = agent._verify_criteria_on_page(
        task=task,
        url="http://127.0.0.1:8080/",
        page_text="MediCare Online Pharmacy Catalog Explore Medicines",
    )
    assert satisfied is True
    assert "visual ux inspection" in reason.lower()



