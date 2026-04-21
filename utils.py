import json
from google import genai
from collections import defaultdict

services_file = 'services.json'
categories_file = 'categories.json'
# Initialize client
client = genai.Client(
    api_key=""
)

delimiter = "####"
step_2_system_message_content = f"""
You are a classification assistant for a Digital Marketing Agency.
You will be provided with user queries related to marketing services.
Each query will be delimited with {delimiter} characters.
Output a python lit of objects, where each object has \
the following format:
 'category': <one of Digital Marketing Agency,\
    Crypto Marketing Agency,\
    Search Engine Optimization,\
    Content Marketing Agency,\
    Social Media Marketing, and Lead Generation Agency>,
OR
  'services':<a list of services that must \
  be found in the allowed services below>

where the categories and proucts must \
be found in marketing services\
If a service is mention, it must be associated with \
the correct category in the allowed services list below.
If no services or categories are found, output an \
empty list

Allowed services:

Digital Marketing Agency:
- Full Service Marketing
- Online Branding
- Performance Marketing

Crypto Marketing Agency:
- Token Promotion
- NFT Marketing
- Blockchain PR

Search Engine Optimization:
- On-Page SEO
- Off-Page SEO
- Technical SEO
- Local SEO

Content Marketing Agency:
- Blog Writing
- Copywriting
- Video Content
- Email Marketing Content

Social Media Marketing:
- Organic Social Media
- Paid Social Ads
- Influencer Marketing
- Social Media Management

Lead Generation Agency:
- B2B Lead Generation
- B2C Lead Generation
- Email Outreach
- Funnel Optimization

Only output the list of objects, with nothing else
"""

step_2_system_message = {'role':'system', 'content': step_2_system_message_content}    


step_4_system_message_content = f"""
    You are a Digital Marketing expert assistant.

    STRICT RULES:
    - You MUST explain ALL requested services mentioned in the user query
    - You MUST NOT skip any service
    - You MUST cover EVERY service from the provided service information
    - If multiple services are present, explain each one separately

    IMPORTANT:
    Before answering, list all services internally and ensure ALL are covered.
    
    FORMAT STRICTLY:
    
    For EACH service:
    
    ### <Service Name>
    Description: ...
    Key Features:
    - ...
    - ...
    Use Case: ...
    
    DO NOT summarize.
    DO NOT skip.
    DO NOT merge services.
    
    If you skip even one service, the answer is WRONG.
"""

step_4_system_message = {'role':'system', 'content': step_4_system_message_content}    

step_6_system_message_content = f"""
    You are an evaluator.

Check if the response explains ALL services listed in the "Agent response".

Rules:
- If ALL services mentioned in the response are explained → Y
- If ANY service is missing → N

Ignore wording differences.
Ignore minor formatting issues.

Return ONLY:
Y or N
"""

step_6_system_message = {'role':'system', 'content': step_6_system_message_content}    


def safe_json_loads(text):
    try:
        if not text or text.strip() == "":
            return None
        
        # Remove markdown if present
        text = text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text)
    except json.JSONDecodeError:
        print("Invalid JSON from model:", text)
        return None

def get_chat_response(messages, model="gemini-2.5-flash-lite",temperature=0,max_output_tokens=1200):
    # Combine messages into one prompt string
    prompt = ""
    for msg in messages:
        prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"

    # Call Gemini model
    response = client.models.generate_content(
        model=model,
        contents=prompt,  # string prompt
        config={
            "temperature": temperature,   #Set temperature here
            "max_output_tokens": max_output_tokens  #set token limit here
        }
    )

    # Return generated text
    return response.text  #use .text, not .contents or .output_text

def create_categories():
    categories_dict = {
      "Digital Marketing Agency": [
        "Full Service Marketing",
        "Online Branding",
        "Performance Marketing"
      ],
      "Crypto Marketing Agency": [
        "Token Promotion",
        "NFT Marketing",
        "Blockchain PR"
      ],
      "Search Engine Optimization": [
        "On-Page SEO",
        "Off-Page SEO",
        "Technical SEO",
        "Local SEO"
      ],
      "Content Marketing Agency": [
        "Blog Writing",
        "Copywriting",
        "Video Content",
        "Email Marketing Content"
      ],
      "Social Media Marketing": [
        "Organic Social Media",
        "Paid Social Ads",
        "Influencer Marketing",
        "Social Media Management"
      ],
      "Lead Generation Agency": [
        "B2B Lead Generation",
        "B2C Lead Generation",
        "Email Outreach",
        "Funnel Optimization"
      ]
    }
    
    with open(categories_file, 'w') as file:
        json.dump(categories_dict, file)
        
    return categories_dict


def get_categories():
    with open(categories_file, 'r') as file:
            categories = json.load(file)
    return categories


def get_service_list():
    """
    Used in L4 to get a flat list of services
    """
    services = get_services()
    service_list = []
    for service in services.keys():
        service_list.append(service)
    
    return service_list

def get_services_and_category():
    """
    Used in L5
    """
    services = get_services()
    services_by_category = defaultdict(list)
    for service_name, service_info in services.items():
        category = service_info.get('category')
        if category:
            services_by_category[category].append(service_info.get('name'))
    
    return dict(services_by_category)

def get_services():
    with open(services_file, 'r') as file:
        services = json.load(file)
    return services

def find_category_and_service(user_input,services_and_category):
    delimiter = "####"
    system_message = f"""
    You are a classification assistant for a Digital Marketing Agency.
    You will be provided with user queries related to marketing services.
    Each query will be delimited with {delimiter} characters.
    Output a python lit of objects, where each object has \
    the following format:
     'category': <one of Digital Marketing Agency,\
        Crypto Marketing Agency,\
        Search Engine Optimization,\
        Content Marketing Agency,\
        Social Media Marketing, and Lead Generation Agency>,
    OR
      'services':<a list of services that must \
      be found in the allowed services below>
    
    where the categories and proucts must \
    be found in marketing services\
    If a service is mention, it must be associated with \
    the correct category in the allowed services list below.
    If no services or categories are found, output an \
    empty list

    The allowed services are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of services that are within that category.
    Allowed services: {services_and_category}
    
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_chat_response(messages)

def find_category_and_service_only(user_input,services_and_category):
    delimiter = "####"
    system_message = f"""
    You are a classification assistant for a Digital Marketing Agency.
    You will be provided with user queries related to marketing services.
    Each query will be delimited with {delimiter} characters.
    Output a python lit of objects, where each object has \
    the following format:
     'category': <one of Digital Marketing Agency,\
        Crypto Marketing Agency,\
        Search Engine Optimization,\
        Content Marketing Agency,\
        Social Media Marketing, and Lead Generation Agency>,
    OR
      'services':<a list of services that must \
      be found in the allowed services below>
    
    where the categories and proucts must \
    be found in marketing services\
    If a service is mention, it must be associated with \
    the correct category in the allowed services list below.
    If no services or categories are found, output an \
    empty list

    Allowed services: 
    
    Digital Marketing Agency:
    - Full Service Marketing
    - Online Branding
    - Performance Marketing
    
    Crypto Marketing Agency:
    - Token Promotion
    - NFT Marketing
    - Blockchain PR
    
    Search Engine Optimization:
    - On-Page SEO
    - Off-Page SEO
    - Technical SEO
    - Local SEO
    
    Content Marketing Agency:
    - Blog Writing
    - Copywriting
    - Video Content
    - Email Marketing Content
    
    Social Media Marketing:
    - Organic Social Media
    - Paid Social Ads
    - Influencer Marketing
    - Social Media Management
    
    Lead Generation Agency:
    - B2B Lead Generation
    - B2C Lead Generation
    - Email Outreach
    - Funnel Optimization
    
    Only output the list of objects, nothing else.
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_chat_response(messages)

def get_services_from_query(user_msg):
    """
    Code from L5, used in L8
    """
    services_and_category = get_services_and_category()
    delimiter = "####"
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, Audio Equipment, Cameras and Camcorders>,
    OR
        'services': <a list of services that must be found in the allowed services below>

    Where the categories and services must be found in the customer service query.
    If a service is mentioned, it must be associated with the correct category in the allowed services list below.
    If no services or categories are found, output an empty list.

    The allowed services are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of services that are within that category.
    Allowed services: {services_and_category}

    """
    
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    ] 
    category_and_service_response = get_chat_response(messages)
    
    return category_and_service_response


# service look up (either by category or by service within category)
def get_service_by_name(name):
    services = get_services()
    return services.get(name, None)

def get_services_by_category(category):
    services = get_services()
    return [service for service in services.values() if service["category"] == category]

def get_mentioned_service_info(data_list):
    """
    Used in L5 and L6
    """
    service_info_l = []

    if data_list is None:
        return service_info_l

    for data in data_list:
        try:
            if "services" in data:
                services_list = data["services"]
                for service_name in services_list:
                    service = get_service_by_name(service_name)
                    if service:
                        service_info_l.append(service)
                    else:
                        print(f"Error: service '{service_name}' not found")
            elif "category" in data:
                category_name = data["category"]
                category_services = get_services_by_category(category_name)
                for service in category_services:
                    service_info_l.append(service)
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return service_info_l



def read_string_to_list(input_string):
    if input_string is None:
        return None

    try:
        input_string = input_string.replace("'", "\"")  # Replace single quotes with double quotes for valid JSON
        data = json.loads(input_string)
        return data
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None

def generate_output_string(data_list):
    output_string = ""

    if data_list is None:
        return output_string

    for data in data_list:
        try:
            if "services" in data:
                services_list = data["services"]
                for service_name in services_list:
                    service = get_service_by_name(service_name)
                    if service:
                        output_string += json.dumps(service, indent=4) + "\n"
                    else:
                        print(f"Error: service '{service_name}' not found")
            elif "category" in data:
                category_name = data["category"]
                category_services = get_services_by_category(category_name)
                for service in category_services:
                    output_string += json.dumps(service, indent=4) + "\n"
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return output_string

# Example usage:
#service_information_for_user_message_1 = generate_output_string(category_and_service_list)
#print(service_information_for_user_message_1)

def answer_user_msg(user_msg,service_info):
    """
    Code from L5, used in L6
    """
    delimiter = "####"
    system_message = f"""
    You are a classification assistant for a Digital Marketing Agency. \
    You will be provided with user queries related to marketing services. \
    Make sure to ask the user relevant follow-up questions.
    """
    # user_msg = f"""
    # tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also what tell me about your tvs"""
    messages =  [  
    {'role':'system', 'content': system_message},   
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    {'role':'assistant', 'content': f"Relevant service information:\n{service_info}"},   
    ] 
    response = get_chat_response(messages)
    return response

def create_services():
    """
        Create services dictionary and save it to a file named services.json
    """
    # service information
    # fun fact: all these services are fake and were generated by a language model
    services = {
        "Full Service Marketing": {
            "name":"Full Service Marketing",
          "category": "Digital Marketing Agency",
          "description": "Comprehensive marketing solution covering all digital channels.",
          "features": [
            "SEO + Social Media + Ads",
            "Content Strategy",
            "Campaign Management",
            "Analytics & Reporting"
          ],
          "use_case": "Businesses looking for complete end-to-end marketing support"
        },
        "Online Branding": {
            "name":"Online Branding",
          "category": "Digital Marketing Agency",
          "description": "Building a strong and consistent online brand presence.",
          "features": [
            "Brand Identity Design",
            "Reputation Management",
            "Visual Branding",
            "Audience Positioning"
          ],
          "use_case": "Startups and businesses wanting brand recognition"
        },
        "Performance Marketing": {
            "name":"Performance Marketing",
          "category": "Digital Marketing Agency",
          "description": "Data-driven marketing focused on measurable results.",
          "features": [
            "ROI Optimization",
            "Conversion Tracking",
            "A/B Testing",
            "Paid Campaign Optimization"
          ],
          "use_case": "Businesses focused on leads and sales growth"
        },
    
        "Token Promotion": {
          "name":"Token Promotion",
          "category": "Crypto Marketing Agency",
          "description": "Marketing campaigns to promote crypto tokens.",
          "features": [
            "Community Building",
            "Exchange Listings Promotion",
            "Airdrops Campaigns",
            "Telegram/Discord Growth"
          ],
          "use_case": "Crypto projects launching new tokens"
        },
        "NFT Marketing": {
            "name":"NFT Marketing",
          "category": "Crypto Marketing Agency",
          "description": "Promoting NFT collections and increasing visibility.",
          "features": [
            "Influencer Promotion",
            "Whitelist Campaigns",
            "Discord Engagement",
            "Marketplace Optimization"
          ],
          "use_case": "NFT creators and digital artists"
        },
        "Blockchain PR": {
            "name":"Blockchain PR",
          "category": "Crypto Marketing Agency",
          "description": "Public relations for blockchain-based projects.",
          "features": [
            "Press Releases",
            "Media Coverage",
            "Crypto News Publishing",
            "Reputation Management"
          ],
          "use_case": "Blockchain startups seeking credibility"
        },
    
        "On-Page SEO": {
            "name":"On-Page SEO",
          "category": "Search Engine Optimization",
          "description": "Optimizing website elements for better search rankings.",
          "features": [
            "Keyword Optimization",
            "Meta Tags",
            "Content Optimization",
            "Internal Linking"
          ],
          "use_case": "Improving website visibility on search engines"
        },
        "Off-Page SEO": {
            "name": "Off-Page SEO",
          "category": "Search Engine Optimization",
          "description": "Building authority through external sources.",
          "features": [
            "Backlink Building",
            "Guest Posting",
            "Social Signals",
            "Directory Submissions"
          ],
          "use_case": "Increasing domain authority and rankings"
        },
        "Technical SEO": {
            "name":"Technical SEO",
          "category": "Search Engine Optimization",
          "description": "Improving backend website performance.",
          "features": [
            "Site Speed Optimization",
            "Mobile Optimization",
            "Crawlability Fixes",
            "Structured Data"
          ],
          "use_case": "Fixing technical issues affecting SEO"
        },
        "Local SEO": {
            "name":"Local SEO",
          "category": "Search Engine Optimization",
          "description": "Optimizing for local search results.",
          "features": [
            "Google Business Profile",
            "Local Listings",
            "Reviews Management",
            "Location Keywords"
          ],
          "use_case": "Businesses targeting local customers"
        },
    
        "Blog Writing": {
            "name":"Blog Writing",
          "category": "Content Marketing Agency",
          "description": "Creating informative blog content.",
          "features": [
            "SEO Blogs",
            "Topic Research",
            "Content Calendar",
            "Keyword Integration"
          ],
          "use_case": "Driving organic traffic through content"
        },
        "Copywriting": {
            "name":"Copywriting",
          "category": "Content Marketing Agency",
          "description": "Writing persuasive marketing content.",
          "features": [
            "Sales Copy",
            "Landing Pages",
            "Ad Copy",
            "Brand Messaging"
          ],
          "use_case": "Improving conversions and engagement"
        },
        "Video Content": {
            "name":"Video Content",
          "category": "Content Marketing Agency",
          "description": "Creating engaging video-based content.",
          "features": [
            "Explainer Videos",
            "Short-form Content",
            "YouTube Videos",
            "Editing & serviceion"
          ],
          "use_case": "Boosting engagement through visuals"
        },
        "Email Marketing Content": {
            "name":"Email Marketing Content",
          "category": "Content Marketing Agency",
          "description": "Creating email campaigns for engagement.",
          "features": [
            "Newsletter Writing",
            "Automation Sequences",
            "Promotional Emails",
            "Personalization"
          ],
          "use_case": "Customer retention and nurturing"
        },
    
        "Organic Social Media": {
          "name":"Organic Social Media",
          "category": "Social Media Marketing",
          "description": "Growing audience without paid ads.",
          "features": [
            "Content Posting",
            "Audience Engagement",
            "Hashtag Strategy",
            "Community Building"
          ],
          "use_case": "Building long-term brand presence"
        },
        "Paid Social Ads": {
            "name":"Paid Social Ads",
          "category": "Social Media Marketing",
          "description": "Running paid ads on social platforms.",
          "features": [
            "Ad Campaign Setup",
            "Audience Targeting",
            "Budget Optimization",
            "Performance Tracking"
          ],
          "use_case": "Generating leads and sales quickly"
        },
        "Influencer Marketing": {
            "name": "Influencer Marketing",
          "category": "Social Media Marketing",
          "description": "Collaborating with influencers for promotion.",
          "features": [
            "Influencer Outreach",
            "Campaign Planning",
            "Content Collaboration",
            "Performance Tracking"
          ],
          "use_case": "Expanding reach through influencers"
        },
        "Social Media Management": {
            "name": "Social Media Management",
          "category": "Social Media Marketing",
          "description": "Managing social media accounts professionally.",
          "features": [
            "Content Scheduling",
            "Profile Optimization",
            "Analytics Tracking",
            "Community Management"
          ],
          "use_case": "Maintaining consistent social presence"
        },
    
        "B2B Lead Generation": {
            "name":"B2B Lead Generation",
          "category": "Lead Generation Agency",
          "description": "Generating leads for business clients.",
          "features": [
            "LinkedIn Outreach",
            "Cold Emailing",
            "CRM Integration",
            "Lead Qualification"
          ],
          "use_case": "Businesses targeting other businesses"
        },
        "B2C Lead Generation": {
            "name":"B2C Lead Generation",
          "category": "Lead Generation Agency",
          "description": "Generating leads from individual consumers.",
          "features": [
            "Landing Pages",
            "Ad Campaigns",
            "Lead Forms",
            "Retargeting"
          ],
          "use_case": "Businesses targeting end customers"
        },
        "Email Outreach": {
            "name":"Email Outreach",
          "category": "Lead Generation Agency",
          "description": "Sending targeted emails to prospects.",
          "features": [
            "Cold Email Campaigns",
            "List Building",
            "Automation Tools",
            "Follow-ups"
          ],
          "use_case": "Direct communication with potential clients"
        },
        "Funnel Optimization": {
            "name":"Funnel Optimization",
          "category": "Lead Generation Agency",
          "description": "Improving conversion funnels.",
          "features": [
            "Conversion Rate Optimization",
            "User Journey Mapping",
            "A/B Testing",
            "Landing Page Optimization"
          ],
          "use_case": "Maximizing conversions and revenue"
        }
      }

    with open(services_file, 'w') as file:
        json.dump(services, file)
        
    return services