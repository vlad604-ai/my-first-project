from aiogram.fsm.state import State, StatesGroup


class LocationInput(StatesGroup):
    waiting = State()


class BookingFlow(StatesGroup):
    address = State()
    note = State()


class ReviewFlow(StatesGroup):
    comment = State()


class ContactFlow(StatesGroup):
    message = State()


class ReportFlow(StatesGroup):
    reason = State()


class QuoteFlow(StatesGroup):
    description = State()
    category = State()
    location = State()
    budget = State()
    urgency = State()


class ProOnboarding(StatesGroup):
    name = State()
    category = State()
    work_mode = State()
    location = State()
    radius = State()
    description = State()


class ProEdit(StatesGroup):
    field = State()
    service_name = State()
    service_duration = State()
    service_price = State()
    hours = State()
    closure = State()
    photos = State()
    quote_amount = State()
    quote_message = State()
    refuse_reason = State()
    review_reply = State()
