import tkinter as tk
from tkinter import ttk, messagebox
import json
import uuid
import math

# Data setup

# Locations
LOCATIONS = ["PUP Main", "CEA", "Hasmin", "iTech", "COC", "PUP LHS", "Condotel"]

# Distance map
DISTANCE_MATRIX = {
    ("PUP Main", "CEA"): 0.5, ("PUP Main", "Hasmin"): 1.0, ("PUP Main", "iTech"): 1.5,
    ("PUP Main", "COC"): 2.0, ("PUP Main", "PUP LHS"): 2.5, ("PUP Main", "Condotel"): 3.0,
    ("CEA", "Hasmin"): 0.5, ("CEA", "iTech"): 1.0, ("CEA", "COC"): 1.5,
    ("CEA", "PUP LHS"): 4.0, ("CEA", "Condotel"): 2.5,
    ("Hasmin", "iTech"): 0.5, ("Hasmin", "COC"): 1.0, ("Hasmin", "PUP LHS"): 1.0,
    ("Hasmin", "Condotel"): 2.0,
    ("iTech", "COC"): 0.5, ("iTech", "PUP LHS"): 1.0, ("iTech", "Condotel"): 1.5,
    ("COC", "PUP LHS"): 0.5, ("COC", "Condotel"): 1.0,
    ("PUP LHS", "Condotel"): 0.5,
}

# Vehicle fare adjustments
VEHICLE_SURCHARGES = {
    "Moto Taxi": 0,
    "Car 4 Seater": 20,
    "Car 6 Seater": 30
}

def get_distance(start, end):
    if start == end:
        return 0
    d = DISTANCE_MATRIX.get((start, end))
    if d is None:
        d = DISTANCE_MATRIX.get((end, start), 0)
    return d

# Booking Data Classes

class Booking:
    def __init__(self, vehicle_type, start, end, distance, cost):
        self.id = str(uuid.uuid4())[:8]
        self.vehicle_type = vehicle_type
        self.start = start
        self.end = end
        self.distance = distance
        self.cost = cost

    def to_dict(self):
        return self.__dict__

class BookingSystem:
    def __init__(self, file="bookings.json"):
        self.file = file
        self.bookings = []
        self.load()

    def calculate_cost(self, vehicle_type, distance):
        base_fare = 50
        if distance > 1:
            additional_km = math.ceil(distance - 1)
            base_fare += additional_km * 10
        surcharge = VEHICLE_SURCHARGES.get(vehicle_type, 0)
        return base_fare + surcharge

    def book(self, vehicle_type, start, end):
        distance = get_distance(start, end)
        cost = self.calculate_cost(vehicle_type, distance)
        booking = Booking(vehicle_type, start, end, distance, cost)
        self.bookings.append(booking)
        self.save()
        return booking

    def cancel(self, booking_id):
        self.bookings = [b for b in self.bookings if b.id != booking_id]
        self.save()

    def save(self):
        with open(self.file, "w") as f:
            json.dump([b.to_dict() for b in self.bookings], f, indent=2)

    def load(self):
        try:
            with open(self.file, "r") as f:
                data = json.load(f)
                for d in data:
                    if "vehicle_type" not in d or "start" not in d or "end" not in d:
                        continue
                    b = Booking(
                        d.get("vehicle_type", "Moto Taxi"),
                        d.get("start"),
                        d.get("end"),
                        d.get("distance", 0),
                        d.get("cost", 0)
                    )
                    b.id = d.get("id", str(uuid.uuid4())[:8])
                    self.bookings.append(b)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

# ---------------------------
# GUI Application
# ---------------------------

class BookingApp:
    def __init__(self, root):
        self.system = BookingSystem()
        self.root = root
        root.title("PUP Ride Booking System")

        # Pick-up
        tk.Label(root, text="Pick-up Location:").grid(row=0, column=0, sticky="w")
        self.pickup = ttk.Combobox(root, values=LOCATIONS, state="readonly")
        self.pickup.grid(row=0, column=1)
        self.pickup.current(0)

        # Drop-off
        tk.Label(root, text="Drop-off Location:").grid(row=1, column=0, sticky="w")
        self.dropoff = ttk.Combobox(root, values=LOCATIONS, state="readonly")
        self.dropoff.grid(row=1, column=1)
        self.dropoff.current(1)

        # Vehicle
        tk.Label(root, text="Vehicle Type:").grid(row=2, column=0, sticky="w")
        self.vehicle = ttk.Combobox(root, values=list(VEHICLE_SURCHARGES.keys()), state="readonly")
        self.vehicle.grid(row=2, column=1)
        self.vehicle.current(0)

        # Buttons
        tk.Button(root, text="Book Ride", command=self.book).grid(row=3, column=0, pady=10)
        tk.Button(root, text="Cancel Selected", command=self.cancel_selected).grid(row=3, column=1)

        # Booking list
        self.listbox = tk.Listbox(root, width=80)
        self.listbox.grid(row=4, column=0, columnspan=2)
        self.refresh()

    def book(self):
        start = self.pickup.get()
        end = self.dropoff.get()
        vehicle_type = self.vehicle.get()

        if start == end:
            messagebox.showerror("Invalid", "Pick-up and drop-off cannot be the same.")
            return

        booking = self.system.book(vehicle_type, start, end)
        self.refresh()

        response = messagebox.askyesno(
            "Booking Confirmed",
            f"Booking ID: {booking.id}\nVehicle: {vehicle_type}\nRoute: {start} → {end}\n"
            f"Distance: {booking.distance:.1f} km\nCost: ₱{booking.cost:.2f}\n\nDo you want to cancel this booking?"
        )

        if response:
            self.system.cancel(booking.id)
            messagebox.showinfo("Cancelled", "Booking has been cancelled.")
            self.refresh()

    def cancel_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showerror("No selection", "Please select a booking to cancel.")
            return
        booking_text = self.listbox.get(selected[0])
        booking_id = booking_text.split()[0]
        confirm = messagebox.askyesno("Confirm", f"Cancel booking {booking_id}?")
        if confirm:
            self.system.cancel(booking_id)
            messagebox.showinfo("Cancelled", "Booking cancelled.")
            self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for b in self.system.bookings:
            self.listbox.insert(
                tk.END,
                f"{b.id} | {b.vehicle_type} | {b.start} → {b.end} | {b.distance:.1f} km | ₱{b.cost:.2f}"
            )
        self.listbox.selection_clear(0, tk.END)

# Run

if __name__ == "__main__":
    root = tk.Tk()
    app = BookingApp(root)
    root.mainloop()
