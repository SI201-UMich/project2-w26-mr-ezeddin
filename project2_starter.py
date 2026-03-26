# SI 201 HW4 (Library Checkout System)
# Your name: Ezeddin kamel
# Your student id:
# Your email: ezeddin@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# e.g.:
# Asked ChatGPT for hints on debugging and for suggestions on overall code structure
#
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
#
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from typing import Any
from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    html_dir = os.path.abspath(os.path.dirname(html_path))

    # Listing ids are stored in local files named listing_<id>.html.
    listing_id_set = set[Any]()
    for fname in os.listdir(html_dir):
        m = re.match(r"listing_(\d+)\.html$", fname)
        if m:
            listing_id_set.add(m.group(1))

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        search_html = f.read()
    soup = BeautifulSoup(search_html, "html.parser")

    # Keep the listing order as it appears in search_results.html.
    ordered_ids: list[str] = []
    anchor_by_id: dict[str, object] = {}
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r"/rooms/(?:plus/)?(\d+)", href)
        if not m:
            continue
        listing_id = m.group(1)
        if listing_id not in listing_id_set or listing_id in seen:
            continue
        seen.add(listing_id)
        ordered_ids.append(listing_id)
        anchor_by_id[listing_id] = a

    result: list[tuple] = []
    for listing_id in ordered_ids:
        title = ""
        if listing_id in anchor_by_id:
            anchor = anchor_by_id[listing_id]
            # The listing title appears directly in the card near the link.
            # We capture the first short "<something> in <location>" phrase.
            nearby_nodes = [anchor.parent] + list(anchor.parents)[:2]
            for anc in nearby_nodes:
                for s in anc.stripped_strings:
                    st = " ".join(s.split())
                    if st.startswith("Over "):
                        continue
                    if re.match(r"^[A-Za-z ]+ in [A-Za-z].+$", st) and 6 <= len(st) <= 90:
                        title = st
                        break
                if title:
                    break
        if not title:
            title = f"Listing {listing_id}"
        result.append((title, listing_id))

    return result

    


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    base_dir = os.path.abspath(os.path.dirname(__file__))
    html_dir = os.path.join(base_dir, "html_files")
    listing_path = os.path.join(html_dir, f"listing_{listing_id}.html")

    with open(listing_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    # policy_number
    m = re.search(
        r"Policy number[^:]{0,40}:\s*<span[^>]*>\s*([^<]+?)\s*</span>",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        val = m.group(1).replace("&nbsp;", " ").strip()
        val = re.sub(r"[\u200b\u200e\u200f\ufeff]", "", val)
        val_clean = re.sub(r"[^A-Za-z0-9-]", "", val)
        low = val_clean.lower()
        if low == "pending":
            policy_number = "Pending"
        elif low == "exempt":
            policy_number = "Exempt"
        else:
            policy_number = val_clean
    elif re.search(r"\bPending\b", text, flags=re.IGNORECASE):
        policy_number = "Pending"
    elif re.search(r"\bExempt\b", text, flags=re.IGNORECASE):
        policy_number = "Exempt"
    else:
        policy_number = "Pending"

    # host_type
    if re.search(r"\bSuperhost\b", text, flags=re.IGNORECASE):
        host_type = "Superhost"
    else:
        host_type = "regular"

    # host_name
    m_host = re.search(r"Hosted by\s+([^<\n\r]+)", text, flags=re.IGNORECASE)
    host_name = m_host.group(1).strip() if m_host else ""

    # room_type
    m_room = re.search(r'property="og:description"\s+content="([^"]*)"', text)
    og_desc = m_room.group(1) if m_room else ""
    og_desc = og_desc.replace("&amp;", "&")
    prefix = og_desc[:140].lower()
    if "entire" in prefix:
        room_type = "Entire Room"
    elif "shared" in prefix:
        room_type = "Shared Room"
    elif "private" in prefix:
        room_type = "Private Room"
    else:
        room_type = "Entire Room"

    # location_rating
    location_rating = 0.0
    for m_rating in re.finditer(r'aria-label="([0-9]+\.[0-9]+) out of 5\.0"', text):
        val = m_rating.group(1)
        window = text[max(0, m_rating.start() - 300) : m_rating.start()].lower()
        if "location" in window:
            try:
                location_rating = float(val)
                break
            except ValueError:
                pass

    return {
        str(listing_id): {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating,
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def create_listing_database(html_path) -> list[tuple]:
   """
   Use prior functions to gather all necessary information and create a database of listings.


   Args:
       html_path (str): The path to the HTML file containing the search results


   Returns:
       list[tuple]: A list of tuples. Each tuple contains:
       (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
   """
   # TODO: Implement checkout logic following the instructions
   # ==============================
   # YOUR CODE STARTS HERE
   # ==============================
   listings = load_listing_results(html_path)
   detailed_data = []
   for listing_title, listing_id in listings:
       details = get_listing_details(listing_id)
       inner = details[str(listing_id)]
       detailed_data.append(
           (
               listing_title,
               str(listing_id),
               inner["policy_number"],
               inner["host_type"],
               inner["host_name"],
               inner["room_type"],
               inner["location_rating"],
           )
       )
   return detailed_data
   # ==============================
   # YOUR CODE ENDS HERE
   # ==============================




def output_csv(data, filename) -> None:
   """
   Write data to a CSV file with the provided filename.


   Sort by Location Rating (descending).


   Args:
       data (list[tuple]): A list of tuples containing listing information
       filename (str): The name of the CSV file to be created and saved to


   Returns:
       None
   """
   # TODO: Implement checkout logic following the instructions
   # ==============================
   # YOUR CODE STARTS HERE
   # ==============================
   header = [
       "Listing Title",
       "Listing ID",
       "Policy Number",
       "Host Type",
       "Host Name",
       "Room Type",
       "Location Rating",
   ]


   sorted_data = sorted(data, key=lambda t: t[6], reverse=True)


   with open(filename, "w", newline="", encoding="utf-8") as f:
       writer = csv.writer(f)
       writer.writerow(header)
       for (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating) in sorted_data:
           writer.writerow(
               [
                   listing_title,
                   listing_id,
                   policy_number,
                   host_type,
                   host_name,
                   room_type,
                   str(location_rating),
               ]
           )
   # ==============================
   # YOUR CODE ENDS HERE
   # ==============================


def avg_location_rating_by_room_type(data) -> dict:
   """
   Calculate the average location_rating for each room_type.


   Excludes rows where location_rating == 0.0 (meaning the rating
   could not be found in the HTML).


   Args:
       data (list[tuple]): The list returned by create_listing_database()


   Returns:
       dict: {room_type: average_location_rating}
   """
   # TODO: Implement checkout logic following the instructions
   # ==============================
   # YOUR CODE STARTS HERE
   # ==============================
   totals = {}
   counts = {}
   for row in data:
       room_type = row[5]
       rating = row[6]
       if rating == 0.0:
           continue
       totals[room_type] = totals.get(room_type, 0.0) + rating
       counts[room_type] = counts.get(room_type, 0) + 1


   return {rt: totals[rt] / counts[rt] for rt in totals}
   # ==============================
   # YOUR CODE ENDS HERE
   # ==============================




def validate_policy_numbers(data) -> list[str]:
   """
   Validate policy_number format for each listing in data.
   Ignore "Pending" and "Exempt" listings.


   Args:
       data (list[tuple]): A list of tuples returned by create_listing_database()


   Returns:
       list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
   """
   # TODO: Implement checkout logic following the instructions
   # ==============================
   # YOUR CODE STARTS HERE
   # ==============================
   invalid = []
   pat1 = re.compile(r"^20\d{2}-00\d{4}STR$")
   pat2 = re.compile(r"^STR-\d{7}$")


   for row in data:
       listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating = row
       if policy_number in ("Pending", "Exempt"):
           continue
       if not (pat1.match(policy_number) or pat2.match(policy_number)):
           invalid.append(str(listing_id))


   return invalid
   # ==============================
   # YOUR CODE ENDS HERE
   # ==============================


# EXTRA CREDIT
def google_scholar_searcher(query):
   """
   EXTRA CREDIT


   Args:
       query (str): The search query to be used on Google Scholar
   Returns:
       List of titles on the first page (list)
   """
   # TODO: Implement checkout logic following the instructions
   # ==============================
   # YOUR CODE STARTS HERE
   # ==============================
   # Extra credit: do a live request. If blocked, return [].
   try:
       resp = requests.get(
           "https://scholar.google.com/scholar",
           params={"q": query},
           timeout=10,
           headers={"User-Agent": "Mozilla/5.0"},
       )
       soup = BeautifulSoup(resp.text, "html.parser")
       titles = []
       for h3 in soup.find_all("h3"):
           txt = " ".join(h3.get_text(" ", strip=True).split())
           if txt:
               titles.append(txt)
       return titles
   except Exception:
       return []
   # ==============================
   # YOUR CODE ENDS HERE
   # ==============================


class TestCases(unittest.TestCase):
   def setUp(self):
       self.base_dir = os.path.abspath(os.path.dirname(__file__))
       self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")


       self.listings = load_listing_results(self.search_results_path)
       self.detailed_data = create_listing_database(self.search_results_path)


   def test_load_listing_results(self):
       # TODO: Check that the number of listings extracted is 18.
       # TODO: Check that the FIRST (title, id) tuple is  ("Loft in Mission District", "1944564").
       self.assertEqual(len(self.listings), 18)
       self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))


   def test_get_listing_details(self):
       html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]


       # TODO: Call get_listing_details() on each listing id above and save results in a list.


       # TODO: Spot-check a few known values by opening the corresponding listing_<id>.html files.
       # 1) Check that listing 467507 has the correct policy number "STR-0005349".
       # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
       # 3) Check that listing 1944564 has the correct location rating 4.9.
       detailed = [get_listing_details(lid) for lid in html_list]


       # listing 467507 policy number
       self.assertEqual(detailed[0][html_list[0]]["policy_number"], "STR-0005349")


       # listing 1944564 host type + room type + location rating
       self.assertEqual(detailed[2][html_list[2]]["host_type"], "Superhost")
       self.assertEqual(detailed[2][html_list[2]]["room_type"], "Entire Room")
       self.assertAlmostEqual(detailed[2][html_list[2]]["location_rating"], 4.9)


   def test_create_listing_database(self):
       # TODO: Check that each tuple in detailed_data has exactly 7 elements:
       # (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)


       # TODO: Spot-check the LAST tuple is ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8).
       for tup in self.detailed_data:
           self.assertEqual(len(tup), 7)


       last = self.detailed_data[-1]
       self.assertEqual(
           last,
           ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8),
       )


   def test_output_csv(self):
       out_path = os.path.join(self.base_dir, "test.csv")


       # TODO: Call output_csv() to write the detailed_data to a CSV file.
       # TODO: Read the CSV back in and store rows in a list.
       # TODO: Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].


       output_csv(self.detailed_data, out_path)


       with open(out_path, "r", newline="", encoding="utf-8") as f:
           reader = csv.reader(f)
           rows = list(reader)


       self.assertGreaterEqual(len(rows), 2)
       self.assertEqual(
           rows[1],
           ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"],
       )


       os.remove(out_path)


   def test_avg_location_rating_by_room_type(self):
       # TODO: Call avg_location_rating_by_room_type() and save the output.
       # TODO: Check that the average for "Private Room" is 4.9.
       avg = avg_location_rating_by_room_type(self.detailed_data)
       self.assertIn("Private Room", avg)
       self.assertAlmostEqual(avg["Private Room"], 4.9)


   def test_validate_policy_numbers(self):
       # TODO: Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
       # TODO: Check that the list contains exactly "16204265" for this dataset.
       invalid_listings = validate_policy_numbers(self.detailed_data)
       self.assertEqual(invalid_listings, ["16204265"])




def main():
   base_dir = os.path.abspath(os.path.dirname(__file__))
   search_results_path = os.path.join(base_dir, "html_files", "search_results.html")
   out_path = os.path.join(base_dir, "airbnb_dataset.csv")
   detailed_data = create_listing_database(search_results_path)
   output_csv(detailed_data, out_path)




if __name__ == "__main__":
   main()
   unittest.main(verbosity=2)



