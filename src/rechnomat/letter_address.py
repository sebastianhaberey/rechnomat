from rechnomat.model import Customer, Seller


def build_address_lines(customer: Customer) -> list[str]:
    """
    Build the recipient address lines for the DIN 5008 address field, top to bottom: name, address
    lines 1-3, postcode/city, and (for non-domestic addresses) the country on its own line.
    """
    name = customer.name if not customer.legal_form else f"{customer.name} {customer.legal_form}"
    address = customer.address
    lines = [name, address.address_line_1]
    if address.address_line_2:
        lines.append(address.address_line_2)
    if address.address_line_3:
        lines.append(address.address_line_3)
    lines.append(f"{address.postcode} {address.city}")
    if address.country_code != "DE":
        lines.append(address.country_code)
    return lines


def build_return_address_line(seller: Seller) -> str:
    """
    Build the small "Rücksendeangabe" line shown above the recipient address in the DIN 5008 address
    field, used so window envelopes show a return address if the letter is undeliverable.
    """
    return f"{seller.name} · {seller.address.address_line_1} · {seller.address.postcode} {seller.address.city}"
