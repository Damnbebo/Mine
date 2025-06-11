import nodemailer from 'nodemailer'
import path from 'path'

// In-memory storage for appointments (resets on server restart)
// Note: For production, consider using a database or external storage service
let appointments = []

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: process.env.SMTP_PORT ? parseInt(process.env.SMTP_PORT) : 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER || 'toshidelay@gmail.com',
    pass: process.env.SMTP_PASS || 'jaqe olxj bzph qcss',
  },
})

function convertTo24Hour(time12h) {
  const [time, modifier] = time12h.split(' ')
  let [hours, minutes] = time.split(':')
  if (hours === '12') {
    hours = '00'
  }
  if (modifier === 'PM') {
    hours = parseInt(hours, 10) + 12
  }
  return `${hours.toString().padStart(2, '0')}:${minutes}`
}

function isConflict(newAppointment) {
  const newTime24 = convertTo24Hour(newAppointment.time)
  const newStart = new Date(newAppointment.date + 'T' + newTime24)
  const newEnd = new Date(newStart.getTime() + newAppointment.duration * 60000)

  console.log('Checking conflict for:', {
    date: newAppointment.date,
    time: newAppointment.time,
    time24: newTime24,
    duration: newAppointment.duration,
    newStart: newStart.toISOString(),
    newEnd: newEnd.toISOString()
  })

  for (const appt of appointments) {
    if (appt.canceled) continue
    
    const apptTime24 = convertTo24Hour(appt.time)
    const apptStart = new Date(appt.date + 'T' + apptTime24)
    const apptEnd = new Date(apptStart.getTime() + appt.duration * 60000)

    console.log('Comparing with existing appointment:', {
      date: appt.date,
      time: appt.time,
      time24: apptTime24,
      duration: appt.duration,
      apptStart: apptStart.toISOString(),
      apptEnd: apptEnd.toISOString()
    })

    if (
      (newStart >= apptStart && newStart < apptEnd) ||
      (newEnd > apptStart && newEnd <= apptEnd) ||
      (newStart <= apptStart && newEnd >= apptEnd)
    ) {
      console.log('CONFLICT DETECTED!')
      return true
    }
  }
  console.log('No conflict found')
  return false
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const {
    name,
    email,
    phone,
    vehicle,
    service,
    date,
    time,
    addons,
    duration,
  } = req.body

  if (
    !name ||
    !email ||
    !phone ||
    !vehicle ||
    !service ||
    !date ||
    !time ||
    !duration
  ) {
    return res.status(400).json({ error: 'Missing required fields' })
  }

  const newAppointment = {
    id: Date.now().toString(),
    name,
    email,
    phone,
    vehicle,
    service,
    date,
    time,
    addons: addons || [],
    duration,
    canceled: false,
  }

  if (isConflict(newAppointment)) {
    return res.status(409).json({ error: 'Appointment time conflicts with an existing booking' })
  }

  appointments.push(newAppointment)

  try {
    // Check if SMTP is properly configured
    const isSmtpConfigured = process.env.SMTP_HOST && 
                            process.env.SMTP_HOST !== 'smtp.example.com' &&
                            process.env.SMTP_USER && 
                            process.env.SMTP_USER !== 'user@example.com'

    if (isSmtpConfigured) {
      const logoPath = path.join(process.cwd(), 'public', 'gardenbstate.png')
      
      // Send email to admin
      await transporter.sendMail({
        from: `"Garden State Detailing" <${process.env.SMTP_USER}>`,
        to: 'toshidelay@gmail.com',
        subject: 'New Detail Appointment Request',
        html: createAdminEmailTemplate(newAppointment),
        attachments: [{
          filename: 'logo.png',
          path: logoPath,
          cid: 'logo'
        }]
      })

      // Send confirmation email to customer
      await transporter.sendMail({
        from: `"Milton from Garden State Detailing" <${process.env.SMTP_USER}>`,
        to: email,
        subject: 'Thanks for Choosing Garden State Detailing!',
        html: createCustomerEmailTemplate(newAppointment),
        attachments: [{
          filename: 'logo.png',
          path: logoPath,
          cid: 'logo'
        }]
      })

      return res.status(200).json({ 
        message: 'Appointment booked successfully! Confirmation emails sent.', 
        appointmentId: newAppointment.id 
      })
    } else {
      // SMTP not configured, but appointment is still booked
      console.log('SMTP not configured. Appointment booked but no emails sent.')
      console.log('Admin notification:', createAdminEmailTemplate(newAppointment))
      console.log('Customer confirmation:', createCustomerEmailTemplate(newAppointment))
      
      return res.status(200).json({ 
        message: 'Appointment booked successfully! (Email configuration needed for confirmations)', 
        appointmentId: newAppointment.id 
      })
    }
  } catch (error) {
    console.error('Email sending error:', error)
    // Still return success since appointment was booked
    return res.status(200).json({ 
      message: 'Appointment booked successfully! (Email sending failed - please check SMTP configuration)', 
      appointmentId: newAppointment.id 
    })
  }
}

// Create professional HTML email templates
function createAdminEmailTemplate(appointment) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Appointment Request</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-width: 120px; height: auto; margin-bottom: 15px; }
        .content { padding: 30px; }
        .appointment-details { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 4px; }
        .detail-row { margin: 10px 0; }
        .label { font-weight: bold; color: #2c3e50; }
        .value { color: #34495e; }
        .footer { background-color: #ecf0f1; padding: 20px; text-align: center; color: #7f8c8d; border-radius: 0 0 8px 8px; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="Garden State Detailing" class="logo">
            <h1>New Appointment Request</h1>
        </div>
        <div class="content">
            <p>Hey Milton,</p>
            <p>You have a new detail request that needs your attention:</p>
            
            <div class="appointment-details">
                <div class="detail-row">
                    <span class="label">Customer:</span> 
                    <span class="value">${appointment.name}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Phone:</span> 
                    <span class="value">${appointment.phone}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Email:</span> 
                    <span class="value">${appointment.email}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Vehicle:</span> 
                    <span class="value">${appointment.vehicle}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Package:</span> 
                    <span class="value">${appointment.service}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Add-ons:</span> 
                    <span class="value">${appointment.addons && appointment.addons.length > 0 ? appointment.addons.join(', ') : 'None'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> 
                    <span class="value">${appointment.date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> 
                    <span class="value">${appointment.time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Duration:</span> 
                    <span class="value">${appointment.duration} minutes</span>
                </div>
            </div>
            
            <p><strong>⏰ Remember to confirm this booking with the customer within 24 hours.</strong></p>
        </div>
        <div class="footer">
            <p>Garden State Detailing - Professional Auto Detailing Services</p>
            <p>Wharton, NJ | (973) 580-0014</p>
        </div>
    </div>
</body>
</html>
  `
}

function createCustomerEmailTemplate(appointment) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Choosing Garden State Detailing</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-width: 120px; height: auto; margin-bottom: 15px; }
        .content { padding: 30px; }
        .appointment-summary { background-color: #f8f9fa; border-left: 4px solid #27ae60; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .detail-row { margin: 10px 0; }
        .label { font-weight: bold; color: #2c3e50; }
        .value { color: #34495e; }
        .highlight { background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .contact-info { background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .footer { background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; }
        .social-links { margin: 15px 0; }
        .social-links a { color: #3498db; text-decoration: none; margin: 0 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:logo" alt="Garden State Detailing" class="logo">
            <h1>Thank You for Choosing Garden State Detailing!</h1>
        </div>
        <div class="content">
            <p>Hi ${appointment.name},</p>
            <p>Thank you for choosing Garden State Detailing! I've received your appointment request and I'm excited to work on your <strong>${appointment.vehicle}</strong>.</p>
            
            <div class="appointment-summary">
                <h3 style="margin-top: 0; color: #27ae60;">📅 Your Appointment Request Details</h3>
                <div class="detail-row">
                    <span class="label">Package:</span> 
                    <span class="value">${appointment.service}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Add-ons:</span> 
                    <span class="value">${appointment.addons && appointment.addons.length > 0 ? appointment.addons.join(', ') : 'None'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> 
                    <span class="value">${appointment.date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> 
                    <span class="value">${appointment.time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Estimated Duration:</span> 
                    <span class="value">${appointment.duration} minutes</span>
                </div>
            </div>
            
            <div class="highlight">
                <p><strong>🕐 What's Next?</strong></p>
                <p>I'll personally reach out within <strong>24 hours</strong> to confirm these details and discuss any specific needs for your vehicle.</p>
            </div>
            
            <div class="contact-info">
                <h3 style="margin-top: 0; color: #2c3e50;">📞 Need to Reach Me?</h3>
                <p><strong>Phone/Text:</strong> (973) 580-0014</p>
                <p><strong>Email:</strong> gardenstatedetailingllc@gmail.com</p>
                <p><strong>Location:</strong> Wharton, NJ</p>
                <p><strong>Hours:</strong> Monday - Saturday, 9:00 AM - 3:30 PM</p>
            </div>
            
            <p>Looking forward to bringing your car back to life!</p>
            <p>Best regards,<br><strong>Milton</strong><br>Garden State Detailing</p>
        </div>
        <div class="footer">
            <p><strong>Garden State Detailing</strong></p>
            <p>Professional Auto Detailing Services</p>
            <p>Wharton, NJ | (973) 580-0014</p>
            <div class="social-links">
                <p>Follow us for tips and updates!</p>
            </div>
        </div>
    </div>
</body>
</html>
  `
}
