# Household Services Web App

## Overview
The **Household Services Web App** is a full-stack platform that connects customers with service professionals for various household tasks. It features role-based dashboards for **Admins, Service Professionals, and Customers**, streamlining service booking, professional management, and request tracking.

## Features

### Admin Dashboard
- Approve or block service professionals.
- Manage user and professional records.
- Monitor service requests and system analytics.

### Service Professional Dashboard
- Register and list services offered.
- Accept or decline service requests.
- Manage booking history and availability.

### Customer Dashboard
- Browse and book household services.
- Track booking status (Requested, Accepted, Closed).
- View professional details before booking.

## Technologies Used
- **Frontend**: HTML, CSS, Bootstrap, Jinja2
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Visualization**: Chart.js (for admin analytics)


## Project Workflow
1. **User Registration & Authentication**
   - Customers and professionals register with unique credentials.
   - Admins manage professional approvals.

2. **Service Booking & Management**
   - Customers browse services and submit booking requests.
   - Professionals accept or reject requests based on availability.

3. **Status Tracking & Notifications**
   - Booking statuses are dynamically updated (Requested, Accepted, Closed).
   - Users receive real-time updates on their requests.

4. **Admin Control & Analytics**
   - Admins monitor user activity, approve/reject professionals, and manage bookings.
   - System analytics provide insights using **Chart.js**.

## Future Enhancements
- Add a payment gateway for seamless transactions.
- Implement live chat between customers and professionals.
- Introduce machine learning for service recommendations.

## Contributors
- Saksham Khurana
