from flask import Flask, render_template_string
import plotly.graph_objs as go
import plotly.io as pio

app = Flask(__name__)

@app.route('/')
def index():
    # Create 9 different Plotly graphs
    charts = []
    for i in range(1, 10):
        if i % 3 == 1:
            data = [go.Bar(x=['A', 'B', 'C'], y=[i * 10, i * 20, i * 30])]
            layout = go.Layout(title=f'Bar Chart {i}')
        elif i % 3 == 2:
            data = [go.Scatter(x=[1, 2, 3], y=[i, i * 2, i * 3], mode='lines+markers')]
            layout = go.Layout(title=f'Scatter Chart {i}')
        else:
            data = [go.Pie(labels=['X', 'Y', 'Z'], values=[i * 10, i * 20, i * 30])]
            layout = go.Layout(title=f'Pie Chart {i}')
        fig = go.Figure(data=data, layout=layout)
        charts.append(pio.to_html(fig, full_html=False))

    # Render the HTML page with tabs
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask + Plotly Tabs</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>Flask + Plotly Example with Tabs</h1>
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="tab1-tab" data-bs-toggle="tab" data-bs-target="#tab1" type="button" role="tab" aria-controls="tab1" aria-selected="true">Tab 1</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="tab2-tab" data-bs-toggle="tab" data-bs-target="#tab2" type="button" role="tab" aria-controls="tab2" aria-selected="false">Tab 2</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="tab3-tab" data-bs-toggle="tab" data-bs-target="#tab3" type="button" role="tab" aria-controls="tab3" aria-selected="false">Tab 3</button>
                </li>
            </ul>
            <div class="tab-content" id="myTabContent">
                <div class="tab-pane fade show active" id="tab1" role="tabpanel" aria-labelledby="tab1-tab">
                    {{ charts[0]|safe }}
                    {{ charts[1]|safe }}
                    {{ charts[2]|safe }}
                </div>
                <div class="tab-pane fade" id="tab2" role="tabpanel" aria-labelledby="tab2-tab">
                    {{ charts[3]|safe }}
                    {{ charts[4]|safe }}
                    {{ charts[5]|safe }}
                </div>
                <div class="tab-pane fade" id="tab3" role="tabpanel" aria-labelledby="tab3-tab">
                    {{ charts[6]|safe }}
                    {{ charts[7]|safe }}
                    {{ charts[8]|safe }}
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(html, charts=charts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5300)