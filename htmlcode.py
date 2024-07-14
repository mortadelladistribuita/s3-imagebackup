<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        h1 {
            text-align: center;
            margin: 20px 0;
        }
        form {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            padding: 10px;
        }
        .gallery img, .gallery video {
            width: 100%;
            height: auto;
            object-fit: cover;
            background-color: #f0f0f0; /* Placeholder background */
        }
    </style>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const mediaElements = Array.from(document.querySelectorAll('img[data-src], video[data-src]'));

            const loadMedia = (element) => {
                if (element.tagName === 'IMG') {
                    element.setAttribute('src', element.getAttribute('data-src'));
                    element.onload = () => {
                        element.removeAttribute('data-src');
                    };
                } else if (element.tagName === 'VIDEO') {
                    element.setAttribute('poster', element.getAttribute('data-thumb'));
                    const source = document.createElement('source');
                    source.setAttribute('src', element.getAttribute('data-src'));
                    source.setAttribute('type', element.getAttribute('data-type'));
                    element.appendChild(source);
                    element.removeAttribute('data-src');
                    element.removeAttribute('data-thumb');
                    element.load();
                }
            };

            const observer = new IntersectionObserver((entries, observer) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        loadMedia(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            });

            // Sort media elements by date (assuming data-date attribute)
            mediaElements.sort((a, b) => new Date(b.getAttribute('data-date')) - new Date(a.getAttribute('data-date')));

            // Observe elements for lazy loading
            mediaElements.forEach((element) => {
                observer.observe(element);
            });
        });
    </script>
</head>
<body>
    <h1>Image Gallery</h1>
    <form method="post">
        <label for="bucket_name">Select Bucket:</label>
        <select id="bucket_name" name="bucket_name">
            {% for bucket in buckets %}
                <option value="{{ bucket }}" {% if bucket == bucket_name %}selected{% endif %}>{{ bucket }}</option>
            {% endfor %}
        </select>
        <label for="year">Select Year:</label>
        <select id="year" name="year">
            <option value="" {% if not year %}selected{% endif %}>All</option>
            {% for y in range(2000, 2025) %}
                <option value="{{ y }}" {% if y|string == year %}selected{% endif %}>{{ y }}</option>
            {% endfor %}
        </select>
        <label for="month">Select Month:</label>
        <select id="month" name="month">
            <option value="" {% if not month %}selected{% endif %}>All</option>
            {% for m in range(1, 13) %}
                <option value="{{ '%02d' % m }}" {% if '%02d' % m == month %}selected{% endif %}>{{ '%02d' % m }}</option>
            {% endfor %}
        </select>
        <button type="submit">Load Media</button>
    </form>
    <hr>
    {% if bucket_name %}
        <h2>Media from Bucket: {{ bucket_name }}</h2>
        {% if year %}<h3>Year: {{ year }}</h3>{% endif %}
        {% if month %}<h3>Month: {{ month }}</h3>{% endif %}
        {% for date, media_list in images.items() %}
            <h3>{{ date }}</h3>
            <div class="gallery">
                {% for media in media_list %}
                    {% if media.type == 'image' %}
                        <img data-src="{{ media.url }}" src="{{ media.thumb }}" data-date="{{ date }}" alt="Image" loading="lazy">
                    {% elif media.type == 'video' %}
                        <video data-src="{{ media.url }}" data-thumb="{{ media.thumb }}" data-type="video/mp4" data-date="{{ date }}" controls loading="lazy"></video>
                    {% endif %}
                {% endfor %}
            </div>
        {% endfor %}
    {% endif %}
</body>
</html>

