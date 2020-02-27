from flask import Flask, render_template, request
import sys

x_length = "4.5";
y_length = "2.0";

if len(sys.argv) == 3:
	x_length = sys.argv[1]
	y_length = sys.argv[2]

print(x_length, y_length)

app = Flask(__name__)

targets = {"A0:A1:A2:A4:A4:A5": ["1.0", "1.0", "0.5", "0.5", "0.5", "0.5"], "B0:B1:B2:B3:B4:B5": ["1.5", "1.5", "0.5", "0.5", "0.5", "0.5"]};

@app.route('/raspberryPi', methods=['GET', 'POST'])
def update_data():
	global targets
	targets = dict()
	print(request)
	targets = request.json.get("data")
	return "ok"
		
	

@app.route('/')
def index():
	global x_length
	global y_length
	print(x_length, y_length)
	canvas = '''
<!DOCTYPE html>
<html lang=en>
    <head>
        <meta charset='UTF-8'/>
        <meta http-equiv='refresh' content='2' />
        <title>IoT Project</title>
    </head>
    <body>
        <h1>Location Tracking System</h1>
        <canvas id='indoor_map' width='%f' height='%f' style='border:1px solid #000000'>
        </canvas>
    </body>
''' % (float(x_length) * 100, float(y_length) * 100)
	global targets
	i = 1
	for mac, coord in targets.items():
		print(mac, coord)
		canvas += "<h5>%d: %s</h5>" % (i, mac)
		canvas += '''
<script>
var c = document.getElementById("indoor_map");
var ctx = c.getContext("2d");
ctx.beginPath();
ctx.arc(%s * 100, (%s * 100) - (%s * 100), 20, 0, 2 * Math.PI);
ctx.stroke();
var ctx2 = c.getContext("2d");
ctx2.font = "30px Arial";
ctx2.fillText("%d", %s * 100 - 10, (%s * 100) - (%s * 100) + 10);
var ctx3 = c.getContext("2d");
ctx3.beginPath();
ctx3.arc(%s * 100, 0, %s * 100, 0, 2 * Math.PI);
ctx3.stroke();
var ctx4 = c.getContext("2d");
ctx4.beginPath();
ctx4.arc(%s * 100, %s * 100, %s * 100, 0, 2 * Math.PI);
ctx4.stroke();
var ctx5 = c.getContext("2d");
ctx5.beginPath();
ctx5.arc(0, 0, %s * 100, 0, 2 * Math.PI);
ctx5.stroke();
var ctx6 = c.getContext("2d");
ctx6.beginPath();
ctx6.arc(0, %s * 100, %s * 100, 0, 2 * Math.PI);
ctx6.stroke();
</script>
''' % (coord[0], y_length, coord[1], i, coord[0], y_length, coord[1], x_length, coord[2], x_length, y_length, coord[3], coord[4], y_length, coord[5])
		i += 1
	return canvas


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
