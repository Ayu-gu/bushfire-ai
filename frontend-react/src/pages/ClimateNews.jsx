import { useEffect, useMemo, useState } from "react";
import {
  Newspaper,
  ExternalLink,
  CloudSun,
  Flame,
  BookOpen,
  RefreshCw,
  CalendarDays,
  ArrowUpRight,
} from "lucide-react";
import "./ClimateNews.css";

const API_URL = "/api/climate-news";

const sources = [
  {
    name: "Bureau of Meteorology",
    description: "Australian weather forecasts, climate observations and warnings.",
    url: "https://www.bom.gov.au/",
    icon: CloudSun,
  },
  {
    name: "CSIRO",
    description: "Australian climate science, environmental research and discoveries.",
    url: "https://www.csiro.au/",
    icon: BookOpen,
  },
  {
    name: "NSW Rural Fire Service",
    description: "Official bushfire information and fire safety updates.",
    url: "https://www.rfs.nsw.gov.au/",
    icon: Flame,
  },
];

const categories = ["All News", "Climate", "Bushfires", "Weather", "Environment"];

function classifyArticle(article) {
  const title = (article.title || "").toLowerCase();

  if (/bushfire|wildfire|fire danger|fire season|hazard reduction|prescribed burn/.test(title)) {
    return "Bushfires";
  }

  if (/climate|global warming|emissions|net zero|carbon|greenhouse|el niño|la niña/.test(title)) {
    return "Climate";
  }

  if (/weather|storm|rainfall|flood|drought|heatwave|cyclone|temperature forecast/.test(title)) {
    return "Weather";
  }

  return "Environment";
}

function articlePriority(article) {
  const category = classifyArticle(article);

  const priorities = {
    Bushfires: 4,
    Climate: 3,
    Weather: 2,
    Environment: 1,
  };

  return priorities[category] || 0;
}

function formatDate(date) {
  if (!date) return "Date unavailable";

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) return "Date unavailable";

  return parsed.toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function ArticleCard({ article, featured = false }) {
  const category = classifyArticle(article);

  return (
    <article className={`climate-article ${featured ? "featured" : ""}`}>
      <div className="climate-article-top">
        <span className={`climate-category climate-category-${category.toLowerCase()}`}>
          {category}
        </span>
        <span className="climate-article-date">
          <CalendarDays size={13} />
          {formatDate(article.publishedAt)}
        </span>
      </div>

      <div className="climate-article-body">
        {featured && <span className="climate-featured-label">FEATURED STORY</span>}

        <h3>{article.title}</h3>

        <p>
          {article.description ||
            "Explore the full article from the original publisher."}
        </p>
      </div>

      <div className="climate-article-footer">
        <span className="climate-article-publisher">
          {article.source}
        </span>

        <a href={article.link} target="_blank" rel="noopener noreferrer">
          Read Article
          <ArrowUpRight size={15} />
        </a>
      </div>
    </article>
  );
}

export default function ClimateNews() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);
  const [fetchedAt, setFetchedAt] = useState(null);
  const [activeCategory, setActiveCategory] = useState("All News");

  useEffect(() => {
    let mounted = true;

    async function loadNews() {
      try {
        const response = await fetch(API_URL);

        if (!response.ok) {
          throw new Error("Unable to retrieve climate news.");
        }

        const data = await response.json();

        if (!mounted) return;

        setArticles(Array.isArray(data.articles) ? data.articles : []);
        setFetchedAt(data.fetchedAt || null);
        setStale(Boolean(data.stale));
        setError("");
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadNews();

    const interval = setInterval(loadNews, 15 * 60 * 1000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const filteredArticles = useMemo(() => {
    return articles
      .filter(
        (article) =>
          activeCategory === "All News" ||
          classifyArticle(article) === activeCategory
      )
      .sort((a, b) => {
        if (activeCategory === "All News") {
          const priorityDifference = articlePriority(b) - articlePriority(a);

          if (priorityDifference !== 0) return priorityDifference;
        }

        return (
          new Date(b.publishedAt || 0).getTime() -
          new Date(a.publishedAt || 0).getTime()
        );
      });
  }, [articles, activeCategory]);

  const [featuredArticle, ...remainingArticles] = filteredArticles;

  return (
    <div className="climate-page">
      <header className="climate-header">
        <div>
          <span className="climate-eyebrow">ENVIRONMENTAL INTELLIGENCE</span>
          <h1>Climate News</h1>
          <p>
            Explore Australian climate developments, bushfire information
            and environmental research from trusted sources.
          </p>
        </div>

        <span className="climate-header-badge">
          <Newspaper size={16} />
          Climate Intelligence
        </span>
      </header>

      <section className="climate-news-section">
        <div className="climate-news-heading">
          <div>
            <h2>Latest Environmental News</h2>
            <p>
              Real articles sourced from The Conversation Australia.
              {fetchedAt && ` Updated ${formatDate(fetchedAt)}.`}
              {stale && " Showing cached articles; the latest refresh failed."}
            </p>
          </div>

          <span className="climate-news-count">
            {filteredArticles.length} articles
          </span>
        </div>

        <div className="climate-filters">
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              className={activeCategory === category ? "active" : ""}
              onClick={() => setActiveCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="climate-state">
            <RefreshCw size={22} />
            <p>Loading the latest climate news...</p>
          </div>
        ) : error ? (
          <div className="climate-state">
            <p>{error}</p>
          </div>
        ) : filteredArticles.length === 0 ? (
          <div className="climate-state">
            <p>No articles currently match this category.</p>
          </div>
        ) : (
          <>
            <ArticleCard article={featuredArticle} featured />

            <div className="climate-articles-grid">
              {remainingArticles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          </>
        )}
      </section>

      <section className="climate-sources">
        <div className="climate-section-heading">
          <h2>Trusted Australian Sources</h2>
          <p>Explore official climate, weather and bushfire information.</p>
        </div>

        <div className="climate-source-grid">
          {sources.map((source) => {
            const Icon = source.icon;

            return (
              <a
                className="climate-source-card"
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                key={source.name}
              >
                <div className="climate-source-icon">
                  <Icon size={22} />
                </div>

                <h3>{source.name}</h3>
                <p>{source.description}</p>

                <span className="climate-source-link">
                  Visit official website
                  <ExternalLink size={15} />
                </span>
              </a>
            );
          })}
        </div>
      </section>
    </div>
  );
}
