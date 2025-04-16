package service

import (
	"errors"
	"log"

	"github.com/IBM/sarama"
)

type KafkaProducer struct {
	asyncProducer sarama.AsyncProducer
}

func NewKafkaProducer(brokers []string) (*KafkaProducer, error) {
	config := sarama.NewConfig()
	config.Producer.Return.Successes = true
	config.Producer.Retry.Max = 3

	producer, err := sarama.NewAsyncProducer(brokers, config)
	if err != nil {
		return nil, err
	}

	go func() {
		for err := range producer.Errors() {
			log.Printf("Failed to send message: %v", err)
		}
	}()

	return &KafkaProducer{asyncProducer: producer}, nil
}

func (p *KafkaProducer) SendMessage(topic string, key string, value []byte) error {
	select {
	case p.asyncProducer.Input() <- &sarama.ProducerMessage{
		Topic: topic,
		Key:   sarama.StringEncoder(key),
		Value: sarama.ByteEncoder(value),
	}:
		return nil
	default:
		return errors.New("KAFKA PRODUCER CHANNEL IS FULL")
	}
}

func (p *KafkaProducer) Close() error {
	return p.asyncProducer.Close()
}
